# houdini_render_dependency
HQueue를 활용해 종속성이 있는 Houdini 노드들을 효율적으로 렌더하고, 렌더가 끝나면 Shotgrid에 렌더 경로를 업로드한다.

## 주요 기능
1. 사용자가 우선순위를 직접 지정해 노드의 의존성 관리
2. 디버깅창 및 알림 메시지를 활용한 작업 모니터링
3. GUI창 종료시, 렌더링 프로세스는 백그라운드에서 계속 진행
4. Shotgrid 업로드 자동화

## 설치 및 실행
- 모듈 설치    
```
pip install shotgun-api3
```     
~/hfs[버전]/scripts/python 에 shotgun_api3폴더 붙여넣기

<br>

- 실행 : controller.py     
후디니 내 python pannel에 추가 후 실행     
```
import site
import importlib
from hutil.Qt import QtWidgets
site.addsitedir('controller.py가 위치한 폴더 경로')

import controller
importlib.reload(controller)

t = controller.Controller()

def onCreateInterface():
    global t
    return t
```

## 제작자
soojin_seong
- github : https://github.com/secondnewbie
