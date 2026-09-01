#!/usr/bin/env python3
"""Maintain non-secret state for yongge-vps-node."""
from __future__ import annotations
import argparse, json, os
from pathlib import Path

STATE = Path(os.environ.get("YONGGE_VPS_NODE_STATE", Path.home()/".codex"/"state"/"yongge-vps-node"/"nodes.json"))


def load():
    if not STATE.exists():
        return {"domain": "", "cloudflare": {}, "nodes": {}}
    return json.loads(STATE.read_text(encoding="utf-8"))


def save(data):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("path")
    sub.add_parser("list")
    g=sub.add_parser("get"); g.add_argument("node")
    u=sub.add_parser("upsert")
    u.add_argument("node")
    for k in ["hostname","host","ssh_user","ssh_port","root_domain","cf_account_id","cf_zone_id","tunnel_name","tunnel_id","vmess_port","vmess_path","subscription_url","last_status"]:
        u.add_argument(f"--{k.replace('_','-')}")
    d=sub.add_parser("delete"); d.add_argument("node")
    args=ap.parse_args()
    data=load()
    if args.cmd=="path":
        print(STATE); return
    if args.cmd=="list":
        print(json.dumps(data, ensure_ascii=False, indent=2)); return
    if args.cmd=="get":
        print(json.dumps(data.get("nodes",{}).get(args.node,{}), ensure_ascii=False, indent=2)); return
    if args.cmd=="delete":
        data.setdefault("nodes",{}).pop(args.node, None); save(data); print(f"deleted {args.node}"); return
    if args.cmd=="upsert":
        nodes=data.setdefault("nodes",{})
        cur=nodes.setdefault(args.node,{"name":args.node})
        for key,val in vars(args).items():
            if key in {"cmd","node"} or val in {None,""}: continue
            if key in {"ssh_port","vmess_port"}:
                try: val=int(val)
                except ValueError: pass
            if key in {"root_domain","cf_account_id","cf_zone_id"}:
                if key=="root_domain": data["domain"]=val
                else: data.setdefault("cloudflare",{})[key.replace("cf_","")]=val
            cur[key]=val
        save(data)
        print(json.dumps(cur, ensure_ascii=False, indent=2))

if __name__=="__main__":
    main()
