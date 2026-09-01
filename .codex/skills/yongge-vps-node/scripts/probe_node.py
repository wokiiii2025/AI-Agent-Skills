#!/usr/bin/env python3
"""Small probe helpers for yongge-vps-node."""
from __future__ import annotations
import argparse, socket, ssl, sys, urllib.request

def tcp(host, port, timeout=8):
    with socket.create_connection((host, port), timeout=timeout): return True

def https(host, timeout=12):
    ctx=ssl.create_default_context()
    req=urllib.request.Request(f"https://{host}/", headers={"User-Agent":"yongge-vps-node-probe"})
    try:
        urllib.request.urlopen(req, timeout=timeout, context=ctx).read(1)
        return "http-ok"
    except Exception as e:
        return f"https-result: {type(e).__name__}: {e}"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("host")
    ap.add_argument("--tcp", type=int, action="append", default=[])
    ap.add_argument("--https", action="store_true")
    args=ap.parse_args()
    for p in args.tcp:
        try: tcp(args.host,p); print(f"tcp {args.host}:{p} ok")
        except Exception as e: print(f"tcp {args.host}:{p} fail {e}"); sys.exitcode=1
    if args.https:
        print(https(args.host))
if __name__=="__main__": main()
