"""Keep HMM option help concise without changing option values or defaults."""
def shorten(schema):
 descriptions={
  'IncludeDir0':['설치한 DLC 중 목록에서 가장 위의 항목을 선택하세요. 없으면 DLC 없음을 선택하세요.'],
  'IncludeDir1':['UnleasHD 1440p와 함께 쓸 때 켜세요.','모드 순서: 한국어 패치 → UnleasHD.'],
  'IncludeDir3':['타이틀·오프닝에 사용할 로고를 선택하세요.'],
 }
 for group in schema['Groups']:
  for element in group['Elements']:
   if element['Name'] in descriptions:element['Description']=descriptions[element['Name']]
 for row in schema['Enums']['WorldMapVariant']:
  row['Description']=['DLC를 설치하지 않았다면 선택하세요.'] if row['Value'].endswith('BaseGame') else ['설치한 DLC 중 목록에서 가장 위의 항목을 선택하세요.']
 for row in schema['Enums']['UnleasHDCompatibility']:row['Description']=[]
 for row in schema['Enums']['TitleLogoVariant']:
  value=row['Value'].split('/')[-1]
  row['Description']=[{'Default':'게임 또는 다른 모드의 로고를 사용합니다.','Original':'영어 원본 로고를 사용합니다.','Japanese':'일본어 원본 로고를 사용합니다.','Korean':'한국어 로고를 타이틀·오프닝에 적용합니다.','Custom':'한국어 로고를 타이틀·오프닝에 적용합니다.'}[value]]
 return schema
