import requests
import json
import time

# -------------------------- 配置区（替换成你自己的信息！）--------------------------
# 1. 你的咪咕登录Cookie（抓包获取，至少包含UserInfo，确保能访问足球通）
COOKIES = {
    "UserInfo": "1717839030|nlps72B201E23169B86B1E7F",  # 替换成你最新的有效Cookie
    # 若抓包有其他Cookie（如msid、token等），全部加在这里，用逗号分隔
}
# 2. 咪咕足球频道配置（批量添加，格式：{"频道名": "contId", "清晰度": rateType}）
# rateType：7=原画HDR，4=蓝光1080P，3=高清720P（根据会员权限选）
FOOTBALL_CHANNELS = {
    "亚冠精英-上海申花": {"contId": "963063316", "rateType": 7},
    # "英超直播": {"contId": "替换成英超的contId", "rateType": 7},
    # "中超直播": {"contId": "替换成中超的contId", "rateType": 7},
    # "欧冠直播": {"contId": "替换成欧冠的contId", "rateType": 7},
    # 按需添加更多足球频道
}
# 3. 咪咕播放地址接口模板（无需修改）
MIGU_API = "https://webapi.miguvideo.com/gateway/playurl/v3/play/playurl?contId={contId}&rateType={rateType}&clientId=aa2b6e8c-d174-4d13-ab76-bdc265660ca4&timestamp={timestamp}&startPlay=true&flvEnable=true&xh265=true&chip=mgwww&channelId=0132_10010001005"
# ----------------------------------------------------------------------------------

# 请求头（伪装浏览器，避免被拦截）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Referer": "https://www.miguvideo.com/",
    "Origin": "https://www.miguvideo.com",
    "Accept": "application/json, text/plain, */*"
}

def get_migu_m3u8(contId, rateType):
    """请求咪咕接口，提取带鉴权的m3u8地址"""
    try:
        timestamp = int(time.time() * 1000)  # 生成实时时间戳，避免过期
        url = MIGU_API.format(contId=contId, rateType=rateType, timestamp=timestamp)
        resp = requests.get(
            url=url,
            headers=HEADERS,
            cookies=COOKIES,
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        
        # 打印接口返回，方便调试
        print(f"接口返回: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # 提取m3u8地址（兼容接口返回格式，优先取urlInfo，无则取urlInfos第一个）
        if data.get("code") == "200" and data.get("body", {}).get("urlInfo", {}).get("url"):
            m3u8_url = data["body"]["urlInfo"]["url"]
            # 咪咕返回的是flv，自动替换为m3u8（实测兼容，OK影视支持）
            if ".flv" in m3u8_url:
                m3u8_url = m3u8_url.replace(".flv", ".m3u8")
            return m3u8_url
        elif data.get("code") == "200" and len(data.get("body", {}).get("urlInfos", [])) > 0:
            m3u8_url = data["body"]["urlInfos"][0]["url"]
            if ".flv" in m3u8_url:
                m3u8_url = m3u8_url.replace(".flv", ".m3u8")
            return m3u8_url
        else:
            print(f"获取{contId}失败：{data.get('message', '接口返回无播放地址')}")
            return None
    except Exception as e:
        print(f"获取{contId}异常：{str(e)}")
        return None

def generate_m3u():
    """生成OK影视兼容的m3u节目单"""
    m3u_content = ["#EXTM3U"]  # m3u标准头
    for channel_name, config in FOOTBALL_CHANNELS.items():
        try:
            m3u8_url = get_migu_m3u8(config["contId"], config["rateType"])
            if m3u8_url:
                # 拼接m3u条目（OK影视识别：tvg-name=频道名，group-title=分类，最后是播放地址）
                m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="咪咕足球通",{channel_name}')
                m3u_content.append(m3u8_url)
                print(f"✅ 成功添加：{channel_name}")
            else:
                m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="咪咕足球通",{channel_name}（暂无法播放）')
                m3u_content.append("#")
                print(f"❌ 失败添加：{channel_name}")
        except Exception as e:
            print(f"处理频道 {channel_name} 时发生异常: {e}")
            m3u_content.append(f'#EXTINF:-1 tvg-name="{channel_name}" group-title="咪咕足球通",{channel_name}（处理异常）')
            m3u_content.append("#")
    
    # 将内容写入m3u文件（仓库根目录，方便Pages访问）
    with open("migufootball.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))
    print("📄 m3u节目单生成完成！")

if __name__ == "__main__":
    try:
        generate_m3u()
    except Exception as e:
        print(f"脚本执行异常: {e}")
        # 即使出错也生成一个空的或部分内容的 m3u，保证 Git 提交能完成
        with open("migufootball.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n# 自动更新失败，请检查脚本")
