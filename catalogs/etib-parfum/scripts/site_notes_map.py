"""Note -> photo theme for the «новинки»-style site cards.
Each theme: (key, Pinterest query, photogenic score 1..5, words that map a catalogue note to it). First match wins."""
THEMES = [
 # citrus
 ('bergamot', 'bergamot citrus fruit aesthetic', 4, ['бергамот']),
 ('grapefruit', 'grapefruit slices aesthetic', 5, ['грейпфрут']),
 ('mandarin', 'mandarin tangerine aesthetic', 5, ['мандарин', 'танжерин']),
 ('lemon', 'lemons aesthetic photography', 5, ['лимон', 'цитрон']),
 ('lime', 'limes aesthetic photography', 5, ['лайм']),
 ('yuzu', 'yuzu fruit aesthetic', 4, ['юзу', 'юдзу']),
 ('orange', 'oranges aesthetic photography', 5, ['апельсин', 'цитрусы', 'цедра']),
 ('neroli', 'orange blossom flowers aesthetic', 5, ['нероли', 'апельсиновый цвет', 'цветок апельсина', 'цветок горького апельсина', 'петитгрейн']),
 # fruits / berries
 ('pineapple', 'pineapple aesthetic photography', 5, ['ананас']),
 ('apple', 'green apples aesthetic', 5, ['яблок']),
 ('pear', 'pears aesthetic photography', 5, ['груш']),
 ('peach', 'peaches aesthetic photography', 5, ['персик', 'нектарин', 'абрикос']),
 ('plum', 'plums aesthetic photography', 5, ['слива', 'чернослив']),
 ('cherry', 'cherries aesthetic dark', 5, ['вишн', 'вишнёв', 'вишнев']),
 ('raspberry', 'raspberries aesthetic', 5, ['малин']),
 ('strawberry', 'strawberries aesthetic', 5, ['клубник']),
 ('blackcurrant', 'blackcurrant berries aesthetic', 5, ['смородин']),
 ('blackberry', 'blackberries aesthetic', 5, ['ежевик', 'черник', 'бузин']),
 ('berries', 'red berries aesthetic', 5, ['ягод', 'клюкв', 'крыжовник', 'гренадин']),
 ('passionfruit', 'passion fruit aesthetic', 5, ['маракуй']),
 ('lychee', 'lychee fruit aesthetic', 5, ['личи']),
 ('mango', 'mango aesthetic photography', 5, ['манго', 'папай']),
 ('pitaya', 'dragon fruit pitaya aesthetic', 5, ['питахай', 'карамбол']),
 ('melon', 'melon aesthetic photography', 5, ['дын', 'арбуз']),
 ('coconut', 'coconut aesthetic photography', 5, ['кокос']),
 ('fig', 'figs aesthetic photography', 5, ['инжир']),
 ('pomegranate', 'pomegranate aesthetic', 5, ['гранат']),
 ('kiwi', 'kiwi fruit aesthetic', 4, ['киви']),
 ('quince', 'quince fruit aesthetic', 4, ['айв']),
 ('dates', 'dates fruit aesthetic', 4, ['финик', 'сухофрукт', 'засахаренные фрукты']),
 ('rhubarb', 'rhubarb aesthetic', 4, ['ревен']),
 ('fruits', 'fresh fruits aesthetic', 3, ['фруктов']),
 # flowers
 ('rose', 'roses aesthetic photography', 5, ['роза']),
 ('jasmine', 'jasmine flowers aesthetic', 5, ['жасмин']),
 ('peony', 'peonies aesthetic', 5, ['пион']),
 ('tuberose', 'tuberose flowers aesthetic', 5, ['тубероз']),
 ('gardenia', 'gardenia flower aesthetic', 5, ['гардени']),
 ('lily', 'white lilies aesthetic', 5, ['лили', 'лилия']),
 ('lily_valley', 'lily of the valley aesthetic', 5, ['ландыш']),
 ('freesia', 'freesia flowers aesthetic', 5, ['фрези']),
 ('violet', 'violets flowers aesthetic', 5, ['фиалк']),
 ('iris', 'iris flower aesthetic', 5, ['ирис']),
 ('orchid', 'orchid aesthetic photography', 5, ['орхиде']),
 ('magnolia', 'magnolia aesthetic', 5, ['магноли']),
 ('lotus', 'lotus flower aesthetic', 5, ['лотос']),
 ('ylang', 'ylang ylang flower', 4, ['иланг']),
 ('osmanthus', 'osmanthus flowers aesthetic', 5, ['османтус']),
 ('heliotrope', 'heliotrope purple flowers', 4, ['гелиотроп']),
 ('cyclamen', 'cyclamen flower aesthetic', 4, ['цикламен']),
 ('hyacinth', 'hyacinth flowers aesthetic', 5, ['гиацинт']),
 ('narcissus', 'narcissus flowers aesthetic', 5, ['нарцисс']),
 ('mimosa', 'mimosa flowers aesthetic', 5, ['мимоз']),
 ('frangipani', 'frangipani plumeria aesthetic', 5, ['франжипани', 'тиаре']),
 ('lavender', 'lavender field aesthetic', 5, ['лаванд']),
 ('geranium', 'geranium flowers aesthetic', 4, ['герань', 'пеларгони']),
 ('cherry_blossom', 'cherry blossom aesthetic', 5, ['цветок сливы', 'цветок миндаля', 'цветок персика', 'цветок нектарина', 'сакур']),
 ('lilac', 'lilac flowers aesthetic', 5, ['сирен', 'глицини']),
 ('flowers', 'white flowers aesthetic', 3, ['цвет', 'горошек', 'камели', 'георгин', 'амариллис', 'гибискус', 'жимолост', 'маргаритк', 'ромашк', 'колокольчик', 'датур', 'бархатц', 'липы', 'дрок', 'резед', 'бессмертник', 'хлопк', 'петали']),
 # spices / herbs
 ('pink_pepper', 'pink peppercorns aesthetic', 5, ['розовый перец']),
 ('pepper', 'black peppercorns aesthetic', 4, ['перец', 'паприк']),
 ('cardamom', 'cardamom pods aesthetic', 5, ['кардамон']),
 ('cinnamon', 'cinnamon sticks aesthetic', 5, ['корица', 'кассия']),
 ('ginger', 'ginger root aesthetic', 5, ['имбир']),
 ('nutmeg', 'nutmeg spice aesthetic', 4, ['мускатный орех']),
 ('saffron', 'saffron threads aesthetic', 5, ['шафран']),
 ('clove', 'cloves spice aesthetic', 4, ['гвоздик']),
 ('coriander', 'coriander seeds aesthetic', 3, ['кориандр']),
 ('spices', 'spices aesthetic dark', 4, ['специ', 'пряност', 'пряные']),
 ('mint', 'fresh mint leaves aesthetic', 5, ['мят']),
 ('basil', 'basil leaves aesthetic', 4, ['базилик']),
 ('sage', 'sage herb aesthetic', 4, ['шалфей']),
 ('rosemary', 'rosemary aesthetic', 4, ['розмарин']),
 ('herbs', 'herbs aesthetic green', 3, ['тархун', 'чабрец', 'артемизи', 'полын', 'давана', 'вербен', 'лавр', 'шисо', 'конопл', 'каннабис', 'бучу']),
 ('tea', 'tea leaves aesthetic', 4, ['чай', 'чайн', 'мате']),
 ('green', 'green leaves aesthetic', 3, ['зелён', 'зелен', 'лист', 'гальбанум', 'бамбук', 'тростник', 'огур', 'алоэ']),
 # gourmand
 ('vanilla', 'vanilla pods aesthetic', 5, ['ванил']),
 ('tonka', 'tonka beans aesthetic', 4, ['тонка', 'кумарин']),
 ('praline', 'praline nuts caramel aesthetic', 5, ['пралине', 'миндал', 'фисташ', 'каштан']),
 ('cotton_candy', 'cotton candy pink aesthetic', 5, ['сахарная вата']),
 ('caramel', 'caramel aesthetic', 5, ['карамел', 'сахар', 'жевательн', 'глазур', 'блеск', 'сладкие ноты', 'маршмеллоу', 'пирожн', 'панна', 'мороженое']),
 ('chocolate', 'chocolate aesthetic dark', 5, ['шоколад', 'какао']),
 ('coffee', 'coffee beans aesthetic', 5, ['кофе', 'капучино']),
 ('honey', 'honey aesthetic', 5, ['мёд', 'мед', 'воск']),
 ('cream', 'whipped cream aesthetic', 4, ['сливк', 'молок']),
 ('licorice', 'licorice root aesthetic', 3, ['лакри']),
 ('alcohol', 'cognac glass aesthetic', 5, ['ром', 'коньяк', 'бренди', 'ликёр', 'водк', 'джин', 'текил', 'шампан', 'кока']),
 # woods / resins / other
 ('tobacco', 'tobacco leaves aesthetic', 5, ['табак', 'табач']),
 ('leather', 'leather texture aesthetic', 4, ['кож', 'замш']),
 ('oud', 'agarwood oud aesthetic', 4, ['уд']),
 ('sandalwood', 'sandalwood aesthetic', 4, ['сандал']),
 ('cedar', 'cedar wood aesthetic', 4, ['кедр', 'кипарис', 'можжевел', 'пихт', 'еловая', 'берёз', 'берез']),
 ('vetiver', 'vetiver roots grass aesthetic', 4, ['ветивер']),
 ('patchouli', 'patchouli leaves aesthetic', 4, ['пачули']),
 ('oakmoss', 'moss forest aesthetic', 4, ['мох']),
 ('incense', 'incense smoke aesthetic', 5, ['ладан', 'олибанум', 'мирр', 'дым', 'элеми', 'стиракс', 'опопонакс', 'бальзам', 'смол', 'бензоин', 'лабданум']),
 ('amber', 'amber resin aesthetic', 3, ['амбр']),
 ('sea', 'sea waves aesthetic', 5, ['морск', 'водн', 'вод', 'калон', 'озон', 'соль', 'лёд', 'минерал', 'кремень', 'песок']),
 ('woods', 'wood texture aesthetic', 3, ['древес', 'дерев', 'гваяк', 'палисандр', 'тиков', 'эбен', 'махагони', 'дуб', 'сикомор', 'акигалавуд', 'джордживуд', 'кашмеран']),
 ('musk', 'white silk fabric aesthetic', 2, ['мускус', 'амбретт', 'гельветолид', 'силколид', 'исо-е', 'гедион', 'альдегид', 'цеталокс', 'амилсалицилат', 'махониал', 'животн', 'цибетин', 'нагармот', 'амброфикс', 'амброксан']),
]


def theme(note):
    n = note.lower().strip()
    for key, q, sc, words in THEMES:
        if any(w in n for w in words):
            return key
    return None


QUERY = {k: q for k, q, s, w in THEMES}
SCORE = {k: s for k, q, s, w in THEMES}

OVERRIDE = {'тубероза': 'tuberose', 'индийская тубероза': 'tuberose', 'апельсиновый цвет': 'neroli', 'африканский апельсиновый цвет': 'neroli',
            'цветок апельсина': 'neroli', 'цветок горького апельсина': 'neroli', 'табачный лист': 'tobacco', 'цветок табака': 'tobacco',
            'тростниковый сахар': 'caramel', 'акигалавуд': 'woods', 'джордживуд': 'woods', 'розифолия': 'rose', 'амбраром': 'amber',
            'кока-кола': 'caramel', 'цветок вишни': 'cherry_blossom', 'вишневый ликёр': 'cherry', 'засахаренный лимон': 'lemon'}
_theme = theme


def theme(note):
    n = note.lower().strip()
    return OVERRIDE.get(n) or _theme(n)
