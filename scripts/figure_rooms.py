from pathlib import Path
import json,os
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'results/extended.json').read_text())['primary']
fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(size):
    return ImageFont.truetype(fontpath,size) if os.path.exists(fontpath) else ImageFont.load_default(size=size)
im=Image.new('RGB',(1700,1030),'white');dr=ImageDraw.Draw(im)
black='#151515';red='#9b2c2c';scale=28
for room in [0,1]:
    cx=430+room*840;cy=455
    dr.text((cx,35),f'Room {room+1}',font=font(64),fill=black,anchor='mt')
    x1,x2=cx-11*scale,cx+11*scale;y1,y2=cy-11*scale,cy+11*scale
    dr.rectangle((x1,y1,x2,y2),outline=black,width=5)
    # The north wall of room 1 and south wall of room 2 share a doorway.
    wy=y1 if room==0 else y2
    dr.line((cx-2.5*scale,wy,cx+2.5*scale,wy),fill='white',width=8)
    dr.text((cx,wy+(-17 if room==0 else 17)),'z = -10',font=font(42),fill=black,anchor='mb' if room==0 else 'mt')
    center=12-22*room-11
    for p in data['placements']:
        if not 12-22*(room+1)<p['z']<12-22*room:continue
        x=cx+p['x']*scale;y=cy+(p['z']-center)*scale
        color=red if p['iteration']!=room else black
        if abs(p['rotation'])==90:
            dr.line((x,y-p['w']*scale/2,x,y+p['w']*scale/2),fill=color,width=10)
            dr.text((x+(-20 if p['x']>0 else 20),y),str(p['id']),font=font(58),fill=color,anchor='rm' if p['x']>0 else 'lm')
        else:
            dr.line((x-p['w']*scale/2,y,x+p['w']*scale/2,y),fill=color,width=10)
            dr.text((x,y+(20 if p['z']<center else -20)),str(p['id']),font=font(58),fill=color,anchor='mt' if p['z']<center else 'mb')
    actual=data['rooms'][room]['auditThumbId'];expected=data['evaluation']['thumbnails'][room]['expected']
    dr.text((cx,845),f'Thumbnail {actual}',font=font(53),fill=black,anchor='mt')
    dr.text((cx,915),f'First artwork {expected}',font=font(53),fill=black,anchor='mt')
im.save(ROOT/'results/room_allocation.png',dpi=(400,400))
print(ROOT/'results/room_allocation.png')
