from pathlib import Path
import argparse,json,sys,hashlib
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import numpy as np
R=Path(__file__).resolve().parents[1];W=R/'Build/UITextureWork';W.mkdir(parents=True,exist_ok=True)
source=json.loads((R/'Translation/review/remaining-ui/texture-comparison.json').read_text(encoding='utf8'))
labels=[]
def label(i,box,text,style='white',font='bold',bg=False):labels.append(dict(texture=i,box=box,korean=text,style=style,font=font,background=bg))
def rows(i,texts,step=32,x=0,y=0,width=None,height=None,**kwargs):
    if width is None:width=Image.open(source[i]['english']).width-x
    for j,t in enumerate(texts):
        if t:label(i,[x,y+j*step,x+width,y+j*step+(height or step)],t,**kwargs)
stages=['윈드밀 아일','루프탑 런','드래곤 로드','사바나 시타델','쿨 에지','애리드 샌즈','정글 조이라이드','스카이스크래이퍼 스캠퍼','에그맨 랜드']
for i in (0,32):
    for x in (0,256):
        names=stages if x==0 else ['화이트 아일랜드','오렌지 루프스','드래곤 로드','크레이 캐슬','쿨 에지','핫 데저트','정글 조이라이드','스카이스크래이퍼 스캠퍼','에그맨 랜드']
        rows(i,names,x=x,width=256,font='slant' if i==0 else 'bold')
rows(1,['스테이지','선택'],step=42,width=270,font='slant',style='silver')
rows(2,['미션','실패'],step=42,width=260,font='slant',style='silver')
for i,texts,ends in [(3,['링','에너지','속도','링','시간','점수','횟수','랩 타임'],[0,17,33,47,59,72,84,97,109]),(4,['체력','언리쉬','경험치'],[0,17,33,45])]:
    for t,a,z in zip(texts,ends,ends[1:]):label(i,[0,a,112,z],t)
label(4,[74,92,128,111],'속도');label(4,[68,112,128,128],'바퀴')
for x,texts in [(0,['점수','속도','메달','격파']),(100,['시간','경험치','적']),(199,['링','점프','최고']),(299,['보너스','힘','기술','콤보']),(400,['합계','높이'])]:rows(5,texts,step=24,x=x,width=100,height=24)
label(5,[0,119,36,148],'레벨');label(5,[60,119,140,148],'최대')
rows(5,['최고 점수','최단 기록','최대 격파 수'],step=24,x=199,y=96,width=190)
label(5,[0,149,175,174],'신기록!',style='orange');label(5,[0,174,90,201],'랭크',font='slant')
label(5,[0,201,176,224],'신기록!',style='orange')
label(5,[0,350,292,392],'결과',font='slant',style='silver')
label(5,[0,460,153,489],'쓰러뜨린 적');label(5,[100,489,193,512],'최대 타격 수')
label(5,[198,460,315,489],'최대 콤보');label(5,[198,489,293,512],'실드')
label(6,[284,0,480,78],'출발!',font='slant',style='silver')
for box,t in [([0,80,512,147],'미션 성공!'),([0,147,512,221],'실패!'),([0,221,512,295],'게임 오버'),([68,295,440,374],'준비')]:label(6,box,t,font='slant',style='silver')
for box,t in [([288,392,512,435],'준비'),([0,434,256,473],'실패!'),([397,434,512,473],'출발!'),([0,472,253,512],'게임 오버'),([255,472,512,512],'미션 성공!')]:label(6,box,t,font='slant')
label(7,[0,0,70,24],'보스',style='red')
for box,t,style in [([32,0,220,48],'좋아요!','green'),([0,48,256,98],'멋져요!','gold'),([8,98,245,147],'최고예요!','cyan'),([0,148,254,192],'실패!','silver')]:label(8,box,t,font='slant',style=style)
rows(9,['실드','에너지'],step=16,width=128,height=16)
for n,t in enumerate(['대시','가드','언리쉬','공격','공격','던지기','잡기','점프','더블 점프','걷기','달리기']):label(10,[0,n*26,240,(n+1)*26],t,font='regular')
for n,t in enumerate(['퀵 스텝','라이트 대시','호밍 어택','부스트','앉기','스톰핑','점프','카메라','걷기','달리기','이동']):label(11,[0,n*26,240,(n+1)*26],t,font='regular')
label(12,[190,0,512,39],'로딩 중',style='green');label(12,[84,47,172,73],'힌트');label(12,[0,80,192,120],'미션',style='green')
label(13,[54,0,512,39],'아무 버튼이나 눌러 주세요',style='green')
label(14,[0,0,172,16],'링 에너지');label(15,[0,0,216,16],'가이아 거신')
rows(16,['부스트','가드','공격'],step=32,x=92,y=0,width=105,height=32,font='regular',bg=True)
rows(17,['확인','뒤로','시간 보내기','다음','리플레이','전환','상세','켜기','끄기','시작','대화','플래시','취소'],step=30,width=126,height=30,font='regular')
rows(18,['시간 보내기','사진 찍기','대화 / 사용'],step=30,width=160,font='regular')
for i in (19,25):
    rows(i,['기술 목록','소지품'],step=32,width=183,font='slant')
    rows(i,['공중' if i==19 else '점프 중','가드 중']+(['대시 중','모으기','길게 누르기'] if i==19 else []),step=30,x=128,y=98,width=128,font='regular',bg=True)
label(20,[0,0,230,42],'일시 정지',font='slant',style='silver')
rows(21,['경험치','전투','힘','체력','언리쉬','실드','속도','링 에너지'],step=24,width=128)
label(21,[0,435,76,466],'최대');label(21,[0,466,35,486],'레벨');label(21,[0,486,81,512],'종료',font='slant')
label(22,[0,0,256,42],'능력치',font='slant',style='silver')
for box,t in [([50,0,211,25],'시작 버튼을 누르세요'),([38,26,91,51],'켜기'),([165,26,216,51],'끄기'),([9,52,125,78],'저장 장치'),([164,52,221,78],'새 항목'),([48,78,211,103],'효과음'),([0,103,130,128],'밝기'),([138,103,256,128],'옵션'),([25,128,109,154],'음악'),([128,128,256,154],'자막'),([24,154,108,180],'음성'),([165,154,225,180],'키'),([20,180,111,205],'소리'),([134,180,256,205],'이어하기'),([80,206,180,231],'카메라'),([14,232,117,257],'설치'),([142,232,249,257],'기본'),([60,258,208,283],'좌우'),([8,284,129,309],'상하'),([132,284,256,309],'언어'),([10,310,116,335],'반전'),([150,310,242,335],'시작'),([50,336,204,362],'게임 시작'),([62,362,200,388],'불러오기'),([66,388,200,413],'새 게임'),([52,414,211,440],'저장 장치')]:label(23,box,t,font='regular')
rows(24,['영어','일본어','프랑스어','독일어','이탈리아어','스페인어'],step=26,width=128,font='regular')
label(26,[7,0,64,25],'신상품!',style='orange');rows(26,['구매','판매'],step=30,y=27,width=90)
label(27,[12,0,32,16],'레벨')
media=['도감','설정 자료집','주민 소개','적 도감','기념품','이벤트 갤러리','리플레이 뷰어','BGM 감상','에그맨의 기계','다크 가이아의 부하들']
for i in (28,29):rows(i,media,step=46,width=512,style='gold')
rows(30,['최고 점수','최단 기록','랭크','링'],step=20,y=172,width=110,height=20)
rows(31,['아포토스','스파고니아','춘난','마주리','홀로스카','샤마르','아다바트','엠파이어 시티','에그맨 랜드'],step=32,width=256)
label(33,[0,0,262,32],'월드맵',style='gold');label(33,[495,16,512,32],'레벨')
from ui_texture_layout_v041 import render
parser=argparse.ArgumentParser()
parser.add_argument('--unleashd-source',type=Path)
parser.add_argument('--output',type=Path)
args=parser.parse_args()
if args.unleashd_source:
    names=['mat_mainmenu_en_001.dds','mat_worldmap_en_001.dds','mat_worldmap_en_002.dds','mat_worldmap_en_003.dds']
    for i,name in zip(range(30,34),names):
        path=args.unleashd_source/name
        if not path.is_file():raise FileNotFoundError(path)
        original=Image.open(source[i]['english'])
        hd=Image.open(path)
        if hd.size != (original.width*2,original.height*2):
            raise ValueError(f'Unexpected UnleasHD dimensions for {name}: {hd.size}')
        source[i]['english']=str(path.resolve())
    render(R,(args.output or R/'Build/UnleasHD-Compatibility'),source,labels,
           layout_scale=2,selected_indices=range(30,34))
else:
    render(R,(args.output or W),source,labels)
