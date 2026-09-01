#!/usr/bin/env python3
"""Patch sing-box-yg Clash/Mihomo subscription for fixed Cloudflare Tunnel mode."""
from __future__ import annotations
import argparse, re
from pathlib import Path

def node_start(line): return line.lstrip().startswith("- name:")
def end_section(line):
    s=line.lstrip()
    return s.startswith("proxy-groups:") or s.startswith("rules:")
def block_type(text):
    for t in ["vless","vmess","hysteria2","tuic","anytls"]:
        if re.search(rf"^\s*type:\s*{re.escape(t)}\s*$", text, re.M): return t
    return ""

def patch_block(block, args):
    text="".join(block)
    typ=block_type(text)
    out=[]; inserted_skip=False; inserted_host=False; in_headers=False
    for line in block:
        stripped=line.strip()
        if typ in {"hysteria2","tuic"} and stripped.startswith("ports:"):
            continue
        if typ=="vmess":
            if re.match(r"^\s*server:\s*", line):
                line=re.sub(r"server:\s*.*", f"server: {args.edge_server}", line)
            elif re.match(r"^\s*port:\s*\d+", line):
                line=re.sub(r"port:\s*\d+", "port: 443", line)
            elif re.match(r"^\s*tls:\s*", line):
                line=re.sub(r"tls:\s*\w+", "tls: true", line)
            elif re.match(r"^\s*servername:\s*", line):
                line=re.sub(r"servername:\s*.*", f"servername: {args.hostname}", line)
            elif re.match(r"^\s*Host:\s*", line):
                line=re.sub(r"Host:\s*.*", f"Host: {args.hostname}", line); inserted_host=True
            if stripped.startswith("headers:"):
                in_headers=True
        out.append(line)
        if typ=="vmess" and "servername:" in line and not inserted_skip and "skip-cert-verify: true" not in text:
            indent=re.match(r"^(\s*)", line).group(1)
            out.append(f"{indent}skip-cert-verify: true\n"); inserted_skip=True
        if typ=="hysteria2" and args.hy2_range and re.match(r"^\s*port:\s*\d+", line):
            indent=re.match(r"^(\s*)", line).group(1); out.append(f"{indent}ports: {args.hy2_range}\n")
        if typ=="tuic" and args.tuic_range and re.match(r"^\s*port:\s*\d+", line):
            indent=re.match(r"^(\s*)", line).group(1); out.append(f"{indent}ports: {args.tuic_range}\n")
    if typ=="vmess" and f"Host: {args.hostname}" not in "".join(out):
        # Conservative append under existing headers if present; otherwise leave a clear marker at end of vmess block.
        for idx,l in enumerate(out):
            if l.strip()=="headers:":
                indent=re.match(r"^(\s*)", l).group(1)
                out.insert(idx+1, f"{indent}  Host: {args.hostname}\n")
                break
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--path", default="/etc/s-box/clmi.yaml")
    ap.add_argument("--hostname", required=True)
    ap.add_argument("--edge-server", default="cloudflare-ech.com")
    ap.add_argument("--hy2-range", default="")
    ap.add_argument("--tuic-range", default="")
    args=ap.parse_args()
    p=Path(args.path)
    lines=p.read_text(encoding="utf-8").splitlines(True)
    out=[]; i=0
    while i < len(lines):
        if node_start(lines[i]):
            block=[lines[i]]; i+=1
            while i < len(lines) and not node_start(lines[i]) and not end_section(lines[i]):
                block.append(lines[i]); i+=1
            out.extend(patch_block(block,args)); continue
        out.append(lines[i]); i+=1
    backup=p.with_suffix(p.suffix+".bak")
    backup.write_text("".join(lines), encoding="utf-8")
    p.write_text("".join(out), encoding="utf-8")
    print(f"patched {p}; backup {backup}")

if __name__=="__main__": main()
