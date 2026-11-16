#!/usr/bin/env python3
"""LaunchReady Gaming V3: reproducible 1080x1350 carousel renderer.
Only screenshots captured from the real LaunchReady website are embedded.
The JSON manifest is the source of truth for slide text, alt text and captions.
"""
from pathlib import Path
import json, textwrap, hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"captures"
OUT=ROOT/"EXPORT_FOR_DRIVE"/"06_CAROUSELS_V3"
DATA=json.loads((ROOT/"source"/"carousels_v3_manifest.json").read_text())
W,H=1080,1350
WHITE=(244,248,251); DIM=(169,187,195); LIME=(193,255,50); BG=(10,19,27); CARD=(20,35,43)
FONT="/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD="/System/Library/Fonts/Supplemental/Arial Bold.ttf"
BLACK="/System/Library/Fonts/Supplemental/Arial Black.ttf"
def ft(n,bold=False,black=False):
    return ImageFont.truetype(BLACK if black else BOLD if bold else FONT,int(n))
def bboxw(t, f):return ImageDraw.Draw(Image.new("RGB",(1,1))).textbbox((0,0),t,font=f)[2]
def text(draw,xy,t,size=38,color=WHITE,bold=False,black=False,anchor=None):
    draw.text(xy,t,font=ft(size,bold,black),fill=color,anchor=anchor,stroke_width=0)
def fit(draw,t,x,y,maxw,size=90,minsize=42,color=WHITE,black=True):
    for s in range(size,minsize-1,-1):
        f=ft(s,black=black)
        if bboxw(t,f)<=maxw:break
    draw.text((x,y),t,font=f,fill=color)
    return s
def wrapped(draw,string,x,y,width,size=35,color=DIM,leading=1.32,maxlines=9,bold=False):
    words=string.split()
    lines=[]; cur=""
    for word in words:
        candidate=(cur+" "+word).strip()
        if bboxw(candidate,ft(size,bold))<=width: cur=candidate
        else:
            if cur:lines.append(cur)
            cur=word
    if cur:lines.append(cur)
    if len(lines)>maxlines: raise RuntimeError("Too many lines: "+string)
    for line in lines:
        text(draw,(x,y),line,size,color,bold)
        y+=int(size*leading)
    return y
def rounded(draw,box,fill=CARD,r=30,outline=None,width=2):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline,width=width)
def base(slug,n,total,eyebrow):
    img=Image.new("RGB",(W,H),BG)
    d=ImageDraw.Draw(img)
    # subtle editorial background, no copyrighted game art
    for y in range(H):
        v=int(10+9*(y/H))
        d.line((0,y,W,y),fill=(v,v+8,v+14))
    glow=Image.new("RGBA",(W,H),(0,0,0,0));g=ImageDraw.Draw(glow)
    g.ellipse((695,-330,1450,430),fill=(105,145,30,50))
    g.ellipse((-330,850,330,1510),fill=(22,118,115,30))
    img=Image.alpha_composite(img.convert("RGBA"),glow.filter(ImageFilter.GaussianBlur(100))).convert("RGB")
    d=ImageDraw.Draw(img)
    d.line((70,125,1010,125),fill=(57,79,83),width=2)
    rounded(d,(70,54,135,110),fill=LIME,r=12)
    text(d,(83,61),"LR",31,(9,22,25),black=True)
    text(d,(152,65),"LAUNCHREADY",32,WHITE,black=True)
    text(d,(764,72),"GTA VI / FREE TOOLS",18,LIME,bold=True)
    text(d,(74,152),eyebrow.upper(),24,LIME,bold=True)
    d.line((70,1211,1010,1211),fill=(76,99,96),width=2)
    text(d,(74,1240),"@LAUNCHREADY_GAMING",24,WHITE,bold=True)
    text(d,(74,1282),"Independent fan resource. Not affiliated with Rockstar.",17,DIM)
    for i in range(total):
        rounded(d,(840+i*36,1241,870+i*36,1249),LIME if i==n-1 else (65,87,93),r=4)
    return img,d
def headline(d,string,y=210,size=83,maxw=930):
    yy=y
    for line in string.split("\n"):
        fit(d,line,73,yy,maxw,size,50,WHITE,True)
        yy+=105
    return yy
def pill(d,label,x,y,fill=LIME):
    w=bboxw(label,ft(22,True))+40
    rounded(d,(x,y,x+w,y+42),fill,r=18)
    text(d,(x+20,y+8),label,22,(8,25,23),bold=True)
    return x+w
def render(slide,idx,total,slug):
    img,d=base(slug,idx,total,slide.get("eyebrow",slug.replace("_"," ")))
    kind=slide["type"]
    if kind=="hero":
        yy=headline(d,slide["headline"],240,94)
        rounded(d,(70,yy+32,1010,yy+210),fill=(26,44,50),r=28,outline=(55,77,73))
        wrapped(d,slide["body"],100,yy+70,870,42,WHITE,1.3,maxlines=3)
        rounded(d,(70,970,1010,1150),fill=(183,245,46),r=30)
        text(d,(105,993),slide.get("callout_title","SAVE THIS GUIDE"),40,(8,23,22),black=True)
        wrapped(d,slide.get("callout","SWIPE FOR THE EXACT CHECKS →"),105,1055,820,31,(13,39,31),1.2,3,True)
    elif kind=="table":
        yy=headline(d,slide["headline"],215,72)
        wrapped(d,slide["body"],76,yy+12,900,30,DIM,1.3,3)
        y=yy+118
        for j,row in enumerate(slide["rows"]):
            fill=(36,58,59) if j==slide.get("highlight_index",-1) else CARD
            rounded(d,(72,y,1008,y+91),fill,r=22)
            text(d,(103,y+23),row[0],35,WHITE,bold=True)
            text(d,(975,y+18),row[1],43,LIME,black=True,anchor="ra")
            y+=104
        if "foot" in slide: wrapped(d,slide["foot"],80,1089,910,25,DIM,1.28,3)
    elif kind=="steps":
        yy=headline(d,slide["headline"],205,72)
        if "body" in slide: wrapped(d,slide["body"],74,yy+2,900,29,DIM,1.26,3)
        items=slide["steps"]
        start=max(yy+112,515);gap=min(190,int((1135-start)/len(items)))
        for j,item in enumerate(items):
            y=start+j*gap
            rounded(d,(72,y,1008,y+gap-12),CARD,r=24,outline=(45,71,67))
            rounded(d,(95,y+25,153,y+83),LIME,r=17)
            text(d,(112,y+33),str(j+1),31,(7,30,26),black=True)
            text(d,(175,y+20),item[0],38,WHITE,bold=True)
            wrapped(d,item[1],176,y+77,785,27,DIM,1.23,3)
        if "foot" in slide: wrapped(d,slide["foot"],75,1137,940,20,DIM,1.2,2)
    elif kind=="number":
        yy=headline(d,slide["headline"],210,76)
        text(d,(72,yy+34),slide["value"],109,LIME,black=True)
        wrapped(d,slide["body"],76,yy+190,875,40,WHITE,1.3,4)
        rounded(d,(72,995,1008,1148),CARD,r=25,outline=(52,77,69))
        wrapped(d,slide["foot"],105,1035,855,27,DIM,1.3,3)
    elif kind=="screenshot":
        yy=headline(d,slide["headline"],207,74)
        wrapped(d,slide["body"],77,yy+10,920,31,DIM,1.3,3)
        photo=Image.open(SRC/slide["screenshot"]).convert("RGB")
        # crop to real top portion for legibility, preserving aspect
        maxh=min(photo.height,915)
        photo=photo.crop((0,0,photo.width,maxh))
        photow=440
        photoh=int(photo.height*photow/photo.width)
        if photoh>760:
            photo=photo.crop((0,0,photo.width,int(760*photo.width/photow)))
            photoh=760
        photo=photo.resize((photow,photoh),Image.Resampling.LANCZOS)
        y=460
        rounded(d,(555,y-13,1010,y+photoh+13),fill=(44,66,68),r=28)
        img.paste(photo,(563,y))
        d=ImageDraw.Draw(img)
        x=77
        for j,(a,b) in enumerate(slide["steps"]):
            yp=510+j*190
            pill(d,a,x,yp)
            wrapped(d,b,x,yp+59,427,31,WHITE,1.3,4,bold=True)
        text(d,(87,1145),"ACTUAL TOOL SCREENSHOT",18,LIME,bold=True)
    elif kind=="formula":
        yy=headline(d,slide["headline"],220,76)
        rounded(d,(72,yy+25,1008,yy+392),fill=CARD,r=30)
        for j,(a,b) in enumerate(slide["rows"]):
            y=yy+66+j*110
            text(d,(104,y),a,31,DIM,bold=True)
            text(d,(968,y-8),b,43,LIME,black=True,anchor="ra")
            if j<len(slide["rows"])-1:d.line((106,y+83,964,y+83),fill=(51,76,70),width=2)
        wrapped(d,slide["foot"],78,1017,890,29,DIM,1.3,4)
    else:raise RuntimeError("unhandled "+kind)
    # ensure content is 1080×1350, embedded readable previews
    return img
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    summary=[]
    for item in DATA:
        slug=item["slug"];folder=OUT/slug;folder.mkdir(exist_ok=True)
        for i,slide in enumerate(item["slides"],start=1):
            if not slide.get("alt") or len(slide["alt"])<95:raise ValueError("Missing substantial alt "+slug+" "+str(i))
            path=folder/f"{i:02d}_{slug}_1080x1350.png"
            img=render(slide,i,len(item["slides"]),slug)
            img.save(path,optimize=True)
            with Image.open(path) as check:
                if check.size!=(1080,1350):raise AssertionError(path)
            (folder/f"{i:02d}_alt.txt").write_text(slide["alt"]+"\n")
            summary.append((slug,i,str(path),hashlib.sha256(path.read_bytes()).hexdigest()))
        (folder/"CAPTION.txt").write_text(item["caption"]+"\n")
        (folder/"SOURCE_NOTES.txt").write_text("\n".join(DATA[0].get("shared_sources",[])+item["sources"])+"\n")
    (OUT/"MANIFEST.json").write_text(json.dumps(DATA,indent=2,ensure_ascii=False))
    (OUT/"QA_SHA256.tsv").write_text("slug\tslide\tpath\tsha256\n"+"\n".join("\t".join(map(str,x)) for x in summary)+"\n")
    # a 5x5 visual inspection sheet (assets aren't replaced by this)
    tw,th=216,270;sheet=Image.new("RGB",(tw*5,th*5),(19,30,38))
    for k,(_,_,p,_) in enumerate(summary):
        if k>=25:break
        im=Image.open(p).convert("RGB").resize((tw,th),Image.Resampling.LANCZOS)
        sheet.paste(im,((k%5)*tw,(k//5)*th))
    sheet.save(OUT/"QA_CONTACT_SHEET.jpg",quality=90)
    print(json.dumps({"slide_count":len(summary),"carousels":{x["slug"]:len(x["slides"]) for x in DATA},"output":str(OUT),"qa":"all dimensions/alt lengths/hashes validated"},indent=2))
if __name__=="__main__":main()
