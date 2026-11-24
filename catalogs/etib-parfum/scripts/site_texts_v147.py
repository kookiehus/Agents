"""Staff website texts after catalogue v147: «Как продать» for the 7 fragrances that had none, «Читается» for 21,
groups for 13 cards without them, renamed fragrances updated in tips / trainer / pronunciations,
«Если не подошёл» links pointed at fragrances that exist, tips of removed fragrances dropped.
Usage: python3 site_texts_v147.py <site repo dir>   (then run build_helper.py in the site repo)"""
import sys, json, re
SITE = sys.argv[1]
def rd(f, pre):
    t = open(f'{SITE}/{f}', encoding='utf-8').read(); i = t.index(pre) + len(pre)
    return t[:i], json.JSONDecoder().raw_decode(t[i:])[0]
def wr(f, head, obj, tail=';\n', indent=None):
    open(f'{SITE}/{f}', 'w', encoding='utf-8').write(head + json.dumps(obj, ensure_ascii=False, indent=indent, separators=None if indent else (',', ':')) + tail)
cat = open(f'{SITE}/catalog.html', encoding='utf-8').read(); a = cat.index('/*DATA_START*/') + 14; b = cat.index('/*DATA_END*/')
base = json.loads(cat[a:b]); nm = lambda d: re.sub(r'\s*-\s*unisex$', '', d['name'], flags=re.I)
key = lambda d: d['category'] + '|' + d['number']; byk = {key(d): d for d in base}
th, tips = rd('tips.js', 'window.TIPS='); ph, pron = rd('pron.js', 'window.PRON='); trh, tr = rd('trainer-data.js', 'window.TR=')

# ---- groups for cards that had none
FAM = {'ЖЕНСКИЕ|B25': ['Свежие', 'Цветочные', 'Приятные/нежные/легкие', 'Запах чистоты'], 'ЖЕНСКИЕ|C1': ['Свежие', 'Цветочные', 'Приятные/нежные/легкие'],
       'ЖЕНСКИЕ|E6': ['Сладкие', 'Ягодные', 'Цветочные', 'Ванильные'], 'ЖЕНСКИЕ|H4': ['Свежие', 'Фруктовые', 'Цветочные'], 'ЖЕНСКИЕ|H14': ['Свежие', 'Фруктовые', 'Цветочные'],
       'ЖЕНСКИЕ|M5': ['Цветочные', 'Приятные/нежные/легкие', 'Запах чистоты'], 'ЖЕНСКИЕ|M26': ['Сладкие', 'Фруктовые', 'Гурманские'],
       'ЖЕНСКИЕ|S16': ['Сладкие', 'Фруктовые', 'Цветочные'], 'ЖЕНСКИЕ|V11': ['Сладковатые', 'Фруктовые', 'Ягодные', 'Цветочные'],
       'ЖЕНСКИЕ|V21': ['Сладкие', 'Восточные', 'Цветочные', 'На вечер'], 'МУЖСКИЕ|D18': ['Свежие', 'Сладковатые', 'Нежные/легкие/ненавязчивые'],
       'МУЖСКИЕ|M16': ['Свежие', 'Фужерные', 'Классические/солидные/на каждый день'], 'ПРЕМИУМ|K9': ['УНИСЕКС|Сладкие', 'УНИСЕКС|Восточные сладкие и гурманские', 'УНИСЕКС|Пряные']}
for k, g in FAM.items():
    d = byk[k]
    if not d.get('families'): d['families'] = [x if '|' in x else f"{d['category']}|{x}" for x in g]

# ---- renamed fragrances: old name -> current name everywhere
REN = {}
for x in tr:
    d = byk.get(x['c'] + '|' + x['n'])
    if d and x['nm'] != nm(d): REN[x['nm']] = nm(d); x['nm'] = nm(d)
def ren(s):
    for o, n in sorted(REN.items(), key=lambda p: -len(p[0])): s = s.replace(o, n)
    return s

# ---- pronunciations
PR = {'Givenchy Ange ou Demon Le Secret': 'Живанши Анж у Демон Ле Секре', 'Carolina Herrera La Bomba': 'Каролина Эррера Ла Бомба',
      "Lanvin Eclat d'Arpège": "Ланвин Эклат д'Арпеж", "Givenchy L'Interdit 2018": 'Живанши Лантердит', 'Jo Malone Blackberry & Bay 2012': 'Джо Мэлоун Блэкберри энд Бэй',
      'Juliette Has A Gun Powder Love': 'Джульетта Хэз э Ган Паудер Лав', "Kenzo L'Eau par Kenzo": 'Кензо Ло пар Кензо',
      'Parfums de Marly Delina Exclusif 2018': 'Парфюм де Марли Делина Эксклюзиф', 'Paco Rabanne Fame 2022': 'Пако Рабан Фейм',
      'Donna Trussardi 1994': 'Донна Труссарди', 'Trussardi Donna 2011': 'Труссарди Донна', 'Antonio Banderas King of Seduction 2014': 'Антонио Бандерас Кинг оф Седакшн',
      'Alfred Dunhill Desire Blue': 'Альфред Данхилл Дизайр Блю', 'Jean Paul Gaultier Le Male Elixir': 'Жан-Поль Готье Ле Маль Эликсир',
      "Kenzo L'Eau par Kenzo pour Homme": 'Кензо Ло пар Кензо пур Ом', 'Lacoste L.12.12 White': 'Лакост Эль Твелв Твелв Вайт',
      'Hormone Paris GABA': 'Хормон Пари ГАБА', 'Louis Vuitton Symphony': 'Луи Виттон Симфони', 'Marc-Antoine Barrois Tilia 2024': 'Марк-Антуан Барруа Тилия',
      "By Kilian Angels' Share": 'Бай Килиан Энджелс Шэр', 'By Kilian Apple Brandy on the Rocks': 'Бай Килиан Эппл Бренди он зе Рокс'}
names = {nm(d) for d in base}
pron = {k: v for k, v in pron.items() if k in names or k in {x['nm'] for x in tr}}
for k, v in PR.items(): pron.setdefault(k, v)

# ---- «Как продать» for fragrances without it
def pyr(d): return {k: [n.strip() for n in t.split(',') if n.strip()] for k, t in (d.get('pyr') or [])}
NEW = {
 'ЖЕНСКИЕ|C3': dict(how='Яркий тропический букет: сочная питахайя и ананас, а за ними сливочный франжипани и пион. Сладкий, солнечный, с тёплой ванильной базой.',
   hooks=['Яркий и заметный: на нём делают комплименты.', 'Тропические фрукты поднимают настроение с первой секунды.', 'Ванильная база держит аромат на коже долго.'],
   whom='Для женщин, которые любят сладкие фруктово-цветочные ароматы и не боятся быть заметными. Хорошо для праздников, отпуска и тёплой погоды.',
   pitch='Попробуйте Carolina Herrera La Bomba: сочная питахайя, пион и тёплая ваниль — ярко, празднично и очень женственно. Нанесу вам на блоттер?',
   sim=['C7 Carolina Herrera Good Girl', 'Y1 Yves Saint Laurent Mon Paris', 'S16 Salvatore Ferragamo Incanto Shine']),
 'ЖЕНСКИЕ|J6': dict(how='Сахарная вата и маршмеллоу на чистой мускусной коже: нежно, пудрово и уютно, как мягкий свитер.',
   hooks=['Аромат «обнимашек»: мягкий, уютный, не душный.', 'Сладость пудровая, а не приторная.', 'Мускус и амброксан дают эффект ухоженной кожи.'],
   whom='Для девушек и женщин, которые любят нежные сладкие ароматы. На каждый день, на учёбу и работу, особенно в прохладную погоду.',
   pitch='Попробуйте Juliette Has A Gun Powder Love: маршмеллоу, засахаренный миндаль и мягкий мускус — нежно и уютно. Дать понюхать на блоттере?',
   sim=['K2 Kayali Yum Boujee Marshmallow 81', 'A7 Ariana Grande Cloud Pink 2023', 'L8 Lancome La Vie Est Belle']),
 'МУЖСКИЕ|D18': dict(how='Морская свежесть с сочным личи и мандарином, а в базе мягкая тонка и амбра. Свежий, но с тёплым ласковым шлейфом.',
   hooks=['Свежий и лёгкий, но не «пустой»: в базе есть тепло.', 'Подходит на каждый день: офис, прогулка, спорт.', 'Понравится тем, кто не любит резкие ароматы.'],
   whom='Для мужчин, которые любят свежие морские ароматы с мягкой сладостью. Хорошо на каждый день и в тёплое время года.',
   pitch='Попробуйте Alfred Dunhill Desire Blue: морская свежесть, личи и мягкая тонка — чисто, легко и приятно. Пшикну на блоттер?',
   sim=['G7 Giorgio Armani Acqua Di Gio', 'B8 Bvlgari Aqva Pour Homme', 'A10 Antonio Banderas Blue Seduction']),
 'МУЖСКИЕ|J7': dict(how='Классическая лаванда с мятой утопает в мёде, ванили и табаке. Густой, сладкий, тёплый аромат с мощным шлейфом.',
   hooks=['Очень стойкий и шлейфовый: хватает на весь день и вечер.', 'Медово-табачная сладость звучит дорого и мужественно.', 'Узнаваемый «Ле Маль», но глубже и насыщеннее.'],
   whom='Для мужчин, которые любят сладкие тёплые ароматы с характером. Лучше на вечер, свидания и в холодное время года.',
   pitch='Попробуйте Jean Paul Gaultier Le Male Elixir: лаванда, мёд и табак — тепло, сладко и очень притягательно. Нанесу вам на запястье?',
   sim=['D14 Dior Sauvage Elixir', 'P11 Paco Rabanne One Million', 'E8 Giorgio Armani Emporio Armani Stronger With You']),
 'УНИСЕКС|H2': dict(how='Солнечные цитрусы и лаванда, а в сердце абрикосовый османтус и жасмин. Свежий, светлый, с чистым древесно-амбровым шлейфом.',
   hooks=['Спокойный, «расслабляющий» аромат: хорош для напряжённых дней.', 'Унисекс: подойдёт и ему, и ей.', 'Свежий, но с мягкой цветочной теплотой.'],
   whom='Для тех, кто любит чистые светлые ароматы без резкости. Мужчинам и женщинам, на каждый день, в офис и на отдых.',
   pitch='Попробуйте Hormone Paris GABA: мандарин, лаванда и нежный османтус — светло, спокойно и чисто. Дать понюхать?',
   sim=['J1 Juliette Has a Gun Not A Perfume Superdose 2019', 'L10 Louis Vuitton Afternoon Swim', 'E31 Blue Talisman by Ex Nihilo 2023']),
 'УНИСЕКС|L22': dict(how='Искрящийся грейпфрут и бергамот с острым свежим имбирём. Светлый, бодрящий, прозрачный цитрус.',
   hooks=['Заряжает энергией, как стакан свежевыжатого сока.', 'Лёгкий и чистый: уместен везде и не надоедает.', 'Унисекс: подходит и мужчинам, и женщинам.'],
   whom='Для тех, кто любит свежие цитрусовые ароматы. Отлично на лето, в офис, после спорта.',
   pitch='Попробуйте Louis Vuitton Symphony: грейпфрут, бергамот и имбирь — свежо, бодро и очень элегантно. Пшикнуть на блоттер?',
   sim=['L10 Louis Vuitton Afternoon Swim', "L20 Louis Vuitton L'immensité 2018", 'E31 Blue Talisman by Ex Nihilo 2023']),
 'ПРЕМИУМ|K9': dict(how='Яблоко в бокале бренди со льдом: пряный кардамон, ром и ваниль на сухом кедре. Тёплый, сочный и немного хмельной.',
   hooks=['Необычный «коктейльный» аромат: запоминается сразу.', 'Яблоко и бренди звучат дорого и уютно.', 'Подходит и мужчинам, и женщинам.'],
   whom='Для любителей тёплых сладких ароматов с алкогольными нотами. Лучше осенью и зимой, на вечер и праздники.',
   pitch='Попробуйте By Kilian Apple Brandy on the Rocks: яблоко, бренди и кардамон — тепло, сочно и очень стильно. Нанесу вам на блоттер?',
   sim=["K4 By Kilian Angels' Share", 'T4 Tom Ford Tobacco Vanille', 'M7 Mancera Red Tobacco'])}
for k, t in NEW.items():
    if k not in tips: tips[k] = dict(how=t['how'], whom=t['whom'], pitch=t['pitch'], pyr=pyr(byk[k]), sim=t['sim'], ok=False, hooks=t['hooks'])

# ---- tips: drop removed fragrances, rename, fix «похожие»
tips = {k: v for k, v in tips.items() if k in byk}
ref = {d['number'] + ' ' + nm(d): d for d in base}
GONE = {'P16': 'C7 Carolina Herrera Good Girl', 'G14': 'Y11 Yves Saint Laurent Black Opium', 'G9': 'G10 Giorgio Armani Armani Si', 'Z2': 'Z1 Zadig & Voltaire This is Her', 'B20': 'B3 Britney Spears Fantasy'}
def fix_sim(s, cat):
    s = ren(s)
    if s in ref: return s
    code, old = s.split(' ', 1); c = [d for d in base if d['number'] == code]
    if not c: return GONE.get(code)
    w = set(re.findall(r'\w+', old.lower()))
    c.sort(key=lambda d: (-len(w & set(re.findall(r'\w+', nm(d).lower()))), d['category'] != cat))
    return code + ' ' + nm(c[0])
for k, t in tips.items():
    for f in ('how', 'whom', 'pitch'): t[f] = ren(t[f])
    sims = []
    for s in t.get('sim', []):
        s2 = fix_sim(s, k.split('|')[0])
        if s2 and s2 not in sims and s2 != byk[k]['number'] + ' ' + nm(byk[k]): sims.append(s2)
    t['sim'] = sims
bad = [s for t in tips.values() for s in t['sim'] if s not in ref]
assert not bad, bad
order = ['ЖЕНСКИЕ', 'МУЖСКИЕ', 'УНИСЕКС', 'ПРЕМИУМ']; num = lambda n: int(re.sub(r'\D', '', n) or 0)
tips = dict(sorted(tips.items(), key=lambda p: (order.index(p[0].split('|')[0]), p[0].split('|')[1][0], num(p[0].split('|')[1]))))

cat = cat[:a] + json.dumps(base, ensure_ascii=False, separators=(',', ':')) + cat[b:]
cat = re.sub(r"const VER='\d+'", "const VER='%d'" % int(__import__('time').time() * 1000), cat, count=1)
open(f'{SITE}/catalog.html', 'w', encoding='utf-8').write(cat)
wr('tips.js', th, tips); wr('trainer-data.js', trh, tr)
open(f'{SITE}/pron.js', 'w', encoding='utf-8').write(ph + '{\n' + ',\n'.join(f'{json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}' for k, v in pron.items()) + '\n};\n')
print('renamed', len(REN), '| tips', len(tips), '| pron', len(pron), '| no groups left', [key(d) for d in base if not d.get('families')])
