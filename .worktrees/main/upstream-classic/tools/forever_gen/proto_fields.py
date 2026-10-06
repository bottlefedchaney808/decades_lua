import re
s=open(r"E:/WoW4_SiMs/.worktrees/main/upstream-classic/sim/core/proto/api.pb.go",encoding="utf-8").read()
def fields(name):
    m=re.search(r"type %s struct \{(.*?)\n\}"%name, s, re.S)
    out=[]
    for line in m.group(1).splitlines():
        mm=re.search(r"(\w+)\s+[\*\.\w]+\s+`protobuf:\"json=([^\";]+);", line)
        if mm: out.append((mm.group(1), mm.group(2)))
    return out
for n in ["RaidSimRequest","RaidSimResult"]:
    print("== %s ==" % n)
    for a,b in fields(n): print("  %s = %s" % (a,b))
c=open(r"E:/WoW4_SiMs/.worktrees/main/upstream-classic/sim/core/proto/common.pb.go",encoding="utf-8").read()
def cf(name):
    m=re.search(r"type %s struct \{(.*?)\n\}"%name, c, re.S)
    out=[]
    for line in m.group(1).splitlines():
        mm=re.search(r"(\w+)\s+[\*\.\w]+\s+`protobuf:\"json=([^\";]+);", line)
        if mm: out.append((mm.group(1), mm.group(2)))
    return out
for n in ["Player","EquipmentSpec","ItemSpec","Encounter","PlayerStats"]:
    print("== %s ==" % n)
    for a,b in cf(n): print("  %s = %s" % (a,b))
# Class enum
m=re.search(r"Class_ClassMage\s*=\s*(\d+)", c)
m2=re.search(r"Class_Class(\w+)\s*=\s*1\b", c)
print("Mage enum value:", m.group(1) if m else "?", " class1:", m2.group(1) if m2 else "?")
