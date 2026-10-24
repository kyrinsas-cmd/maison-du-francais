"""Centres DELF-DALF en Chine et sessions 2026, d'après la NEEA (教育部教育考试院), consultée le 2026-10-25 :
- centres : https://www.neea.edu.cn/html1/folder/16103/1132-1.htm (page non datée)
- sessions : avis publiés le 2026-09-04 (novembre), 2026-08-21 (青少版 octobre), avis de juin (inscription à partir du 21 avril).
Relancer = mise à jour par clé ; ce qui a été modifié dans l'admin pour une clé est écrasé, les ajouts faits dans l'admin restent.
"""
from datetime import date

from db import connect

CENTRES = [
    ("blcu", "北京", "Pékin", "北京语言大学 国外考试中心", "Université des langues et cultures de Pékin — centre des examens étrangers", "北京市海淀区学院路15号北京语言大学教1楼", "010-82303550", "http://exam.blcu.edu.cn/rxxz.htm"),
    ("tjnu", "天津", "Tianjin", "天津师范大学", "Université normale de Tianjin", "天津市西青区宾水西道393号 天津师范大学主校区留学生公寓", "022-23540229", "https://gjxy.tjnu.edu.cn/info/1075/4405.htm"),
    ("sufe", "上海", "Shanghai", "上海财经大学", "Université des finances et d'économie de Shanghai", "上海市杨浦区纪念路8号 国际继续教育学院笃行楼1楼", "021-63575388", "https://iec.sufe.edu.cn/tzgg/list.htm"),
    ("njnu", "南京", "Nankin", "南京师范大学外国语学院", "Université normale de Nankin — faculté des langues étrangères", "江苏省南京市鼓楼区宁海路122号 南京师范大学外国语学院500号楼104", "025-83598582", "http://wy.njnu.edu.cn/jxjy/hwks.htm"),
    ("dlufl", "大连", "Dalian", "大连外国语大学考试中心", "Université des langues étrangères de Dalian — centre d'examen", "大连市旅顺南路西段6号 大连外国语大学11号教学楼B区111房间", "0411-86115161、86115162", "https://exam.dlufl.edu.cn/"),
    ("sdu", "济南", "Jinan", "山东大学考试中心 外国语学院", "Université du Shandong — centre d'examen, faculté des langues étrangères", "山东省济南市历城区洪家楼5号 山东大学（洪家楼校区）外国语学院", "0531-89001068", "https://www.flc.sdu.edu.cn/xyzx/tzgg.htm"),
    ("whu", "武汉", "Wuhan", "武汉大学考试中心", "Université de Wuhan — centre d'examen", "湖北省武汉市武昌区珞珈山 武汉大学工学部文澜路四教楼", "027-87348743", "http://exam.whu.edu.cn/"),
    ("uestc", "成都", "Chengdu", "电子科技大学考试中心", "Université des sciences et technologies électroniques de Chine — centre d'examen", "四川省成都市建设北路二段四号 电子科技大学沙河校区主楼中110室", "028-83202611", "https://www.oice.uestc.edu.cn/"),
    ("nwu", "西安", "Xi'an", "西北大学", "Université du Nord-Ouest", "陕西省西安市太白北路229号 西北大学国际合作事业大楼三层", "029-88302774", "https://gj.nwu.edu.cn/tzgg.htm"),
    ("jnu", "广州", "Canton", "暨南大学", "Université de Jinan", "广东省广州市天河区黄埔大道西601号 暨南大学外国语学院第二文科楼216", "020-85220212", "https://fc.jnu.edu.cn/2023/0220/c33833a735895/page.htm"),
]
SESSIONS = [
    ("2026-06", "2026年6月 DELF-DALF 考试", "Session de juin 2026 (DELF-DALF)", "A1 A2 B1 B2 C1 C2",
     "2026年6月（具体日期见考试院通知）", "Juin 2026 (dates dans l'avis de la NEEA)", "4月21日开始报名", "Inscriptions à partir du 21 avril",
     date(2026, 6, 1), "https://www.neea.edu.cn/html1/report/2604/125-1.htm"),
    ("2026-10-jeunes", "2026年10月 DELF-DALF 青少版（Prim、Junior）", "Octobre 2026 : DELF Prim et DELF Junior", "Prim A1.1 A1 A2 · Junior A1 A2 B1 B2",
     "笔试：10月24日上午；口试：10月24日下午、10月25日全天", "Écrit : 24 octobre au matin ; oral : 24 octobre après-midi et 25 octobre",
     "8月26日14:00至9月8日14:00", "Du 26 août 14 h au 8 septembre 14 h (heure de Pékin)", date(2026, 10, 24), "https://www.neea.edu.cn/html1/report/2608/16-1.htm"),
    ("2026-11", "2026年11月 DELF-DALF 考试", "Session de novembre 2026 (DELF-DALF)", "A1 A2 B1 B2 C1 C2",
     "C1、C2：11月7–8日；B2：11月14–15日；A1、A2、B1：11月21–22日", "C1, C2 : 7–8 novembre ; B2 : 14–15 novembre ; A1, A2, B1 : 21–22 novembre",
     "9月9日14:00至9月22日14:00", "Du 9 septembre 14 h au 22 septembre 14 h (heure de Pékin)", date(2026, 11, 7), "https://www.neea.edu.cn/html1/report/2609/30-1.htm"),
]


def seed():
    with connect() as c:
        for i, (k, cz, cf, nz, nf, addr, tel, web) in enumerate(CENTRES):
            c.execute("""INSERT INTO exam_centres (key, city_zh, city_fr, name_zh, name_fr, address, phone, website, sort) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                         ON CONFLICT (key) DO UPDATE SET city_zh=EXCLUDED.city_zh, city_fr=EXCLUDED.city_fr, name_zh=EXCLUDED.name_zh, name_fr=EXCLUDED.name_fr,
                           address=EXCLUDED.address, phone=EXCLUDED.phone, website=EXCLUDED.website""", (k, cz, cf, nz, nf, addr, tel, web, i))
        for k, tz, tf, lv, ez, ef, rz, rf, d, src in SESSIONS:
            c.execute("""INSERT INTO exam_sessions (key, title_zh, title_fr, levels, exams_zh, exams_fr, register_zh, register_fr, first_day, source_url)
                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (key) DO NOTHING""", (k, tz, tf, lv, ez, ef, rz, rf, d, src))
    print(f"centres d'examen : {len(CENTRES)} · sessions : {len(SESSIONS)}")


if __name__ == "__main__":
    seed()
