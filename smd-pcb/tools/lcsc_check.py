"""Check LCSC part numbers / keywords against the JLCPCB parts library (jlcpcb.com/parts backend).
Usage: python3 lcsc_check.py C14877 "16MHz 3225" ...   (prints library type, stock, price)"""
import json, sys, urllib.request
API = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"
def q(keyword, n=10):
    body = json.dumps({"keyword": keyword, "currentPage": 1, "pageSize": n}).encode()
    req = urllib.request.Request(API, data=body, headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=30))
    return d["data"]["componentPageInfo"]["list"] or []
def lib(c):
    t = c.get("componentLibraryType")
    if t == "base": return "Basic"
    return "Pref-Ext" if c.get("preferredComponentFlag") else "Extended"
if __name__ == "__main__":
    for t in sys.argv[1:]:
        print("==", t)
        for c in q(t):
            p = c["componentPrices"][0]["productPrice"] if c.get("componentPrices") else "?"
            print(f"  {c['componentCode']:<9} {lib(c):8} stock={c['stockCount']:<8} ${p:<7} {c.get('componentModelEn','')[:30]:30} {c.get('componentSpecificationEn','')[:14]:14} {c.get('describe','')[:60]}")
