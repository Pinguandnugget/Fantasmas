import sys, json, numpy as np
sys.path.insert(0, 'tools')
from verify_render import *
from PIL import Image, ImageDraw, ImageChops
S='/tmp/claude-0/-home-claude/e2f2062b-407e-5467-ba39-5418acd383f8/scratchpad/'
NEW=S+'out/new/assets/fantasmas/'; OLD=S+'jar/assets/fantasmas/'
colors=['blanco','amarillo','rojo','negro']
views=[('frente',0,10),('3/4',35,15),('lado',90,10),('espalda',180,10)]
report=[]
def ndiff(a,b):
    d=np.asarray(ImageChops.difference(a.convert('RGB'),b.convert('RGB'))).sum(axis=2)
    return int((d>0).sum())
rows_static={}
for c in colors:
    bb=json.load(open(S+f'bb/{c}.bbmodel.json')); tex=Image.open(S+f'bb/{c}.png')
    new=json.load(open(NEW+f'geo/fantasma_{c}.geo.json')); old=json.load(open(OLD+f'geo/fantasma_{c}.geo.json'))
    qa=quads_from_bbmodel(bb,{}); qb=quads_from_geo(new,{}); qo=quads_from_geo(old,{})
    row=[]
    for name,yaw,pit in views:
        ia=render(qa,tex,yaw,pit,size=(300,300),scale=19); ib=render(qb,tex,yaw,pit,size=(300,300),scale=19); io=render(qo,tex,yaw,pit,size=(300,300),scale=19)
        nd=ndiff(ia,ib); report.append((c,'reposo',name,nd)); row.append((name,io,ia,ib,nd))
    rows_static[c]=row
print('--- reposo: pixeles distintos entre .bbmodel (Blockbench) y geo nuevo ---')
for r in report: print(r)
# montaje: por fantasma, una fila: [antes(geo viejo) | bbmodel original | geo nuevo] para frente y 3/4
def label(im,txt):
    im=im.copy(); ImageDraw.Draw(im).text((6,4),txt,fill=(255,255,255,255)); return im
for c in colors:
    cols=[]
    for name,io,ia,ib,nd in rows_static[c][:2]:
        cols += [label(io,f'{c} {name}: ANTES (geo.json viejo)'),label(ia,'Blockbench (.bbmodel)'),label(ib,'AHORA (geo.json nuevo)')]
    W=300; M=Image.new('RGB',(W*3,300*2),(0,0,0))
    for i,im in enumerate(cols): M.paste(im.convert('RGB'),((i%3)*W,(i//3)*300))
    M.save(S+f'out/estatico_{c}.png')
# animaciones: bbmodel(A) vs animation.json(B)
tot=0
frames_out={}
for c in colors:
    bb=json.load(open(S+f'bb/{c}.bbmodel.json')); tex=Image.open(S+f'bb/{c}.png')
    new=json.load(open(NEW+f'geo/fantasma_{c}.geo.json')); ad=json.load(open(NEW+f'animations/fantasma_{c}.animation.json'))
    # animacion de vuelo de referencia: la del bbmodel BLANCO (se reutiliza en rojo/negro)
    bbw=json.load(open(S+'bb/blanco.bbmodel.json'))
    for an in ['golpear','volando','prueba']:
        L=ad['animations']['animation.fantasmas.'+an]['animation_length']
        ts=[0,0.25*L,0.5*L,0.75*L]
        for t in ts:
            if an=='golpear': pa=pose_from_bbmodel(bb,'golpear',t)
            else: pa=pose_from_bbmodel(bbw,'volando',t)
            pb=pose_from_json(ad,'animation.fantasmas.'+an,t)
            ia=render(quads_from_bbmodel(bb if True else bbw,pa),tex,20,10,size=(300,300),scale=19)
            ib=render(quads_from_geo(new,pb),tex,20,10,size=(300,300),scale=19)
            nd=ndiff(ia,ib); tot+=nd
            if nd: print('DIF',c,an,round(t,3),nd)
            frames_out[(c,an,round(t,3))]=(ia,ib)
print('animacion: total de pixeles distintos A vs B =',tot)
import pickle; pickle.dump({k:(a.tobytes(),a.size) for k,(a,b) in frames_out.items()},open(S+'out/_frames.pkl','wb'))
