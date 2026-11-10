"""Final baseline fitting functions, same algorithms; final Elastic Net maximum sweeps = 100000."""
import numpy as np

def standardize(train, test):
    train = np.asarray(train, dtype=float)
    test = np.asarray(test, dtype=float)
    mu = train.mean(axis=0)
    sd = train.std(axis=0)
    sd[sd == 0] = 1.0
    return (train - mu) / sd, (test - mu) / sd

def fit_ols(x_train, y_train, x_test):
    xs_train, xs_test = standardize(x_train, x_test)
    design_train = np.column_stack([np.ones(len(xs_train)), xs_train])
    coef = np.linalg.pinv(design_train) @ np.asarray(y_train, dtype=float)
    design_test = np.column_stack([np.ones(len(xs_test)), xs_test])
    return design_test @ coef

def fit_ridge(x_train, y_train, x_test, alpha):
    xs_train, xs_test = standardize(x_train, x_test)
    y_train = np.asarray(y_train, dtype=float)
    design_train = np.column_stack([np.ones(len(xs_train)), xs_train])
    design_test = np.column_stack([np.ones(len(xs_test)), xs_test])
    penalty = np.eye(design_train.shape[1]) * alpha
    penalty[0, 0] = 0.0
    coef = np.linalg.pinv(design_train.T @ design_train + penalty) @ design_train.T @ y_train
    return design_test @ coef

def soft_threshold(value, penalty):
    if value > penalty:
        return value - penalty
    if value < -penalty:
        return value + penalty
    return 0.0

def fit_elastic_net(x_train, y_train, x_test, alpha, l1_ratio=0.65, max_iter=100000, tol=1e-6):
    xs_train, xs_test = standardize(x_train, x_test)
    y = np.asarray(y_train, dtype=float)
    y_mean = y.mean()
    y_sd = y.std() or 1.0
    ys = (y - y_mean) / y_sd
    n, p = xs_train.shape
    beta = np.zeros(p)

    col_norm = np.sum(xs_train**2, axis=0) / n
    l1 = alpha * l1_ratio
    l2 = alpha * (1.0 - l1_ratio)
    pred = xs_train @ beta
    for _ in range(max_iter):
        old = beta.copy()
        for j in range(p):
            residual = ys - pred + xs_train[:, j] * beta[j]
            rho = np.dot(xs_train[:, j], residual) / n
            new_beta = soft_threshold(rho, l1) / (col_norm[j] + l2)
            pred += xs_train[:, j] * (new_beta - beta[j])
            beta[j] = new_beta
        if np.max(np.abs(beta - old)) < tol:
            break
    return (xs_test @ beta) * y_sd + y_mean

def fit_pcr(x_train, y_train, x_test, n_components):
    xs_train, xs_test = standardize(x_train, x_test)
    u, s, vt = np.linalg.svd(xs_train, full_matrices=False)
    k = min(n_components, vt.shape[0])
    train_scores = xs_train @ vt[:k].T
    test_scores = xs_test @ vt[:k].T
    return fit_ols(train_scores, y_train, test_scores)

def fit_knn(x_train, y_train, x_test, k):
    xs_train, xs_test = standardize(x_train, x_test)
    y = np.asarray(y_train, dtype=float)
    preds = []
    for row in xs_test:
        dist = np.sqrt(np.sum((xs_train - row) ** 2, axis=1))
        idx = np.argsort(dist)[:k]
        weights = 1.0 / (dist[idx] + 1e-6)
        preds.append(np.sum(weights * y[idx]) / np.sum(weights))
    return np.asarray(preds)

def fit_mlp(x_train, y_train, x_test, hidden=8, l2=0.01, lr=0.015, epochs=2500, seed=7):
    xs_train, xs_test = standardize(x_train, x_test)
    y = np.asarray(y_train, dtype=float)
    y_mean = y.mean()
    y_sd = y.std() or 1.0
    ys = ((y - y_mean) / y_sd).reshape(-1, 1)

    rng = np.random.default_rng(seed)
    n, p = xs_train.shape
    w1 = rng.normal(0, 0.12, size=(p, hidden))
    b1 = np.zeros((1, hidden))
    w2 = rng.normal(0, 0.12, size=(hidden, 1))
    b2 = np.zeros((1, 1))

    mw1 = np.zeros_like(w1)
    vw1 = np.zeros_like(w1)
    mb1 = np.zeros_like(b1)
    vb1 = np.zeros_like(b1)
    mw2 = np.zeros_like(w2)
    vw2 = np.zeros_like(w2)
    mb2 = np.zeros_like(b2)
    vb2 = np.zeros_like(b2)
    beta1, beta2, eps = 0.9, 0.999, 1e-8

    for t in range(1, epochs + 1):
        z1 = xs_train @ w1 + b1
        h = np.tanh(z1)
        pred = h @ w2 + b2
        grad = 2.0 * (pred - ys) / n
        gw2 = h.T @ grad + l2 * w2
        gb2 = grad.sum(axis=0, keepdims=True)
        gh = grad @ w2.T
        gz1 = gh * (1.0 - h**2)
        gw1 = xs_train.T @ gz1 + l2 * w1
        gb1 = gz1.sum(axis=0, keepdims=True)

        for param, grad_param, m, v in [
            (w1, gw1, mw1, vw1),
            (b1, gb1, mb1, vb1),
            (w2, gw2, mw2, vw2),
            (b2, gb2, mb2, vb2),
        ]:
            m *= beta1
            m += (1 - beta1) * grad_param
            v *= beta2
            v += (1 - beta2) * (grad_param**2)
            m_hat = m / (1 - beta1**t)
            v_hat = v / (1 - beta2**t)
            param -= lr * m_hat / (np.sqrt(v_hat) + eps)

    pred_test = np.tanh(xs_test @ w1 + b1) @ w2 + b2
    return pred_test.ravel() * y_sd + y_mean
