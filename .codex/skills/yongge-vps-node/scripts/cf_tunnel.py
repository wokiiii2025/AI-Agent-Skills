#!/usr/bin/env python3
"""Ensure one Cloudflare fixed tunnel, DNS record, and optional domain-only subscription paths.

Environment:
  CF_API_TOKEN    required unless --token is supplied
  CF_ACCOUNT_ID   optional if --account-id supplied
  CF_ZONE_ID      optional if --zone-id supplied
  CF_ZONE_NAME    optional; used to discover zone id
"""
from __future__ import annotations
import argparse, json, os, sys, urllib.parse, urllib.request

API="https://api.cloudflare.com/client/v4"

def request(method, path, token, body=None, qs=None):
    url=API+path
    if qs:
        url += "?" + urllib.parse.urlencode(qs)
    data=None
    headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"}
    if body is not None:
        data=json.dumps(body).encode()
    req=urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw=r.read().decode()
    except urllib.error.HTTPError as e:
        raw=e.read().decode(errors="replace")
        raise SystemExit(f"Cloudflare API {method} {path} failed: HTTP {e.code}\n{raw}")
    obj=json.loads(raw) if raw else {}
    if not obj.get("success", True):
        raise SystemExit(f"Cloudflare API {method} {path} failed:\n{json.dumps(obj, ensure_ascii=False, indent=2)}")
    return obj.get("result", obj)

def discover_zone(token, zone_name):
    res=request("GET","/zones",token,qs={"name":zone_name,"per_page":1})
    if not res: raise SystemExit(f"zone not found: {zone_name}")
    return res[0]["id"]

def find_tunnel(token, account_id, name):
    res=request("GET",f"/accounts/{account_id}/cfd_tunnel",token,qs={"name":name,"is_deleted":"false","per_page":50})
    for t in res:
        if t.get("name")==name and not t.get("deleted_at"):
            return t
    return None

def create_tunnel(token, account_id, name):
    return request("POST",f"/accounts/{account_id}/cfd_tunnel",token,{"name":name,"config_src":"cloudflare"})

def build_ingress(hostname, vmess_service, subscription_service=None, sub_token=None):
    ingress=[]
    if subscription_service and sub_token:
        for filename in ("clmi.yaml", "sbox.json", "jhsub.txt"):
            ingress.append({"hostname":hostname,"path":f"/{sub_token}/{filename}","service":subscription_service})
    # Keep generic hostname route after path-specific subscription routes.
    ingress.append({"hostname":hostname,"service":vmess_service})
    ingress.append({"service":"http_status:404"})
    return ingress

def put_config(token, account_id, tunnel_id, hostname, service, subscription_service=None, sub_token=None):
    body={"config":{"ingress":build_ingress(hostname, service, subscription_service, sub_token)}}
    return request("PUT",f"/accounts/{account_id}/cfd_tunnel/{tunnel_id}/configurations",token,body)

def token_for(token, account_id, tunnel_id):
    return request("GET",f"/accounts/{account_id}/cfd_tunnel/{tunnel_id}/token",token)

def ensure_dns(token, zone_id, hostname, target, proxied=True):
    found=request("GET",f"/zones/{zone_id}/dns_records",token,qs={"name":hostname,"per_page":100})
    body={"type":"CNAME","name":hostname,"content":target,"ttl":1,"proxied":proxied}
    cname=None
    for rec in found:
        if rec.get("type")=="CNAME":
            cname=rec
        elif rec.get("type") in {"A","AAAA"}:
            # Cloudflare rejects CNAME creation while address records exist at same name.
            request("DELETE",f"/zones/{zone_id}/dns_records/{rec['id']}",token)
    if cname:
        return request("PATCH",f"/zones/{zone_id}/dns_records/{cname['id']}",token,body)
    return request("POST",f"/zones/{zone_id}/dns_records",token,body)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("ensure", nargs="?")
    ap.add_argument("--node", required=True)
    ap.add_argument("--hostname", required=True)
    ap.add_argument("--service", required=True, help="VMess origin, e.g. http://localhost:2052")
    ap.add_argument("--subscription-service", help="local-only subscription origin, e.g. http://localhost:50177")
    ap.add_argument("--sub-token", help="subscription path token, normally UUID; enables /<token>/clmi.yaml, sbox.json, jhsub.txt")
    ap.add_argument("--token", default=os.environ.get("CF_API_TOKEN"))
    ap.add_argument("--account-id", default=os.environ.get("CF_ACCOUNT_ID"))
    ap.add_argument("--zone-id", default=os.environ.get("CF_ZONE_ID"))
    ap.add_argument("--zone-name", default=os.environ.get("CF_ZONE_NAME"))
    ap.add_argument("--tunnel-name")
    ap.add_argument("--no-proxy", action="store_true")
    ap.add_argument("--show-connector-token", action="store_true")
    args=ap.parse_args()
    if bool(args.subscription_service) ^ bool(args.sub_token):
        raise SystemExit("--subscription-service and --sub-token must be supplied together")
    if not args.token: raise SystemExit("missing CF_API_TOKEN or --token")
    if not args.account_id: raise SystemExit("missing CF_ACCOUNT_ID or --account-id")
    zone_id=args.zone_id or (discover_zone(args.token,args.zone_name) if args.zone_name else None)
    if not zone_id: raise SystemExit("missing CF_ZONE_ID/--zone-id or CF_ZONE_NAME/--zone-name")
    tunnel_name=args.tunnel_name or f"yg-{args.node}"
    tunnel=find_tunnel(args.token,args.account_id,tunnel_name) or create_tunnel(args.token,args.account_id,tunnel_name)
    tunnel_id=tunnel["id"]
    put_config(args.token,args.account_id,tunnel_id,args.hostname,args.service,args.subscription_service,args.sub_token)
    dns=ensure_dns(args.token,zone_id,args.hostname,f"{tunnel_id}.cfargotunnel.com",proxied=not args.no_proxy)
    out={"node":args.node,"hostname":args.hostname,"tunnel_name":tunnel_name,"tunnel_id":tunnel_id,"dns_record_id":dns.get("id"),"dns_target":f"{tunnel_id}.cfargotunnel.com","service":args.service,"ingress":build_ingress(args.hostname,args.service,args.subscription_service,args.sub_token)}
    if args.subscription_service:
        out["subscription_urls"]={name:f"https://{args.hostname}/{args.sub_token}/{name}" for name in ("clmi.yaml","sbox.json","jhsub.txt")}
    if args.show_connector_token:
        out["connector_token"]=token_for(args.token,args.account_id,tunnel_id)
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__=="__main__":
    main()
