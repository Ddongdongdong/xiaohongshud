param()
# 设置 NO_PROXY，让 requests 不走代理访问本地 Chrome CDP
$env:NO_PROXY = "localhost,127.0.0.1"
$env:no_proxy = "localhost,127.0.0.1"

Set-Location "C:\Users\Administrator\Desktop\新建文件夹\XiaohongshuSkills"
uvicorn api.main:app --reload --port 8000
