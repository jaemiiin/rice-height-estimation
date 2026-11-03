"""Read-only scan for personal paths, credential-like strings and unclassified files."""
from pathlib import Path
import argparse, json, re
PROJECT=Path(__file__).resolve().parents[1]
SKIP_TOP={'.git','.venv-analysis','.venv-pixels','.local'}
TEXT_EXT={'.py','.md','.txt','.json','.csv','.yaml','.yml','.toml','.cff','.sha256','.diff'}
PATTERNS={
    'absolute_windows_path': re.compile(r'(?<![A-Za-z])[A-Za-z]:[\\/]'),
    'personal_posix_path': re.compile(r'/(?:Users|home)/[^/\s]+'),
    'private_runtime_or_project_path': re.compile(r'PycharmProjects|codex-runtimes|\.codex[/\\]|lasso회귀'),
    'private_key_block': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'aws_access_key': re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    'github_token': re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b|github_pat_[A-Za-z0-9_]{40,}'),
    'credential_assignment': re.compile(r'(?i)(?:api_key|password|access_token|client_secret)\s*[:=]\s*[\"\'][^\"\']{8,}[\"\']'),
}

def paths(root):
    import os
    for folder, dirs, names in os.walk(root):
        rel=Path(folder).relative_to(root)
        dirs[:]=[d for d in dirs if d not in SKIP_TOP and d!='__pycache__'
                 and not (rel.as_posix()=='results' and d=='runs')]
        for name in names:yield Path(folder)/name

def audit(root):
    issues=[];scanned=0
    for path in paths(root):
        rel=path.relative_to(root).as_posix()
        if path.suffix.lower() not in TEXT_EXT and path.name not in ['.gitignore','.gitattributes']:continue
        # Rule definitions themselves intentionally contain detector patterns.
        if rel=='tools/audit_release.py':continue
        text=path.read_text(encoding='utf-8-sig');scanned+=1
        for number,line in enumerate(text.splitlines(),1):
            for label,pattern in PATTERNS.items():
                if pattern.search(line):issues.append(dict(file=rel,line=number,rule=label))
    return dict(status='PASS' if not issues else 'FAIL',text_files_scanned=scanned,findings=issues,
                scope='Project source, documentation, metadata, reference tables; ignored runtimes and generated runs excluded',
                limitations='Pattern-based screening is not a guarantee that every possible secret has been detected')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=PROJECT);p.add_argument('--report',type=Path)
    a=p.parse_args();result=audit(a.root.resolve())
    if a.report:
        if a.report.exists():raise FileExistsError('Choose a new report path')
        a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    if result['findings']:raise SystemExit(1)

if __name__=='__main__':main()
