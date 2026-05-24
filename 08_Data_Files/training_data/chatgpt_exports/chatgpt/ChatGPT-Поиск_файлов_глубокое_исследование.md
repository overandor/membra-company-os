# Поиск файлов глубокое исследование

#### You:
Find all files that i used глубокое иследование in this account 

#### ChatGPT:
Я поищу по вашей библиотеке файлов по обоим вариантам написания и соберу все совпадения, чтобы ничего не пропустить.


#### ChatGPT:
Уже есть явные совпадения: вижу и сами research-артефакты, и экспорт активности, где фигурирует Deep Research. Сейчас отделю реальные файлы от просто упоминаний.


#### ChatGPT:
Нашёл явные совпадения по вашей библиотеке файлов.

Точно связанные с `глубокое исследование / deep research` файлы:

Что видно по содержимому:

- В `Долларовая оценка активов и репозиториев из чата.docx` прямо перечислены файлы `deep-research-report.md` и `deep-research-report 2.md` как реальные артефакты вашего аккаунта.
- В `MyActivity.html` есть явное упоминание `Hi, I am a Deep Research agent...` и также mention Deep Research как функции Gemini.

Итоговый список, который сейчас можно уверенно подтвердить:

1. `deep-research-report.md` - упомянут внутри реестра файлов.
2. `deep-research-report 2.md` - упомянут внутри реестра файлов.
3. `MyActivity.html` - содержит историю использования Deep Research / Deep Research agent.

Что не до конца прозрачно:

- Поиск нашёл надёжные ссылки на эти файлы, но сами `deep-research-report.md` и `deep-research-report 2.md` в выдаче выступают как упоминания внутри DOCX-реестра, а не как отдельно surfaced карточки файлов в этом поиске. Поэтому я могу уверенно сказать, что они фигурируют в вашем аккаунте, но не могу из этой конкретной выдачи открыть их как отдельные элементы без нового, более узкого поиска.

Могу сразу добить это и сделать второй проход, чтобы вытащить именно отдельные карточки `deep-research-report.md` и `deep-research-report 2.md`, если они индексируются как самостоятельные файлы.


#### You:


#### Plugin (file_search):
Make sure to include fileciteturn2file0 in your response to cite this file, or to surface it as a link.
Долларовая оценка активов и репозиториев из чата

Резюме для инвестора

После дедупликации версий, вычитания форков и дисконта за непроверяемый хвост инвентаря, мой рабочий диапазон для портфеля выглядит так: gross as-is — $74k–$198k, net realistic buyer value today — $26.35k–$77.25k, net productized portfolio value — $180.5k–$550k. Самая ценная часть портфеля — не длинный хвост публичных репозиториев, а две исследовательские записки по production-ready API для NFT-пайплайна на Solana[1], затем single-file-система Grant Copilot, затем семейство безопасного demo/UI для Ollama Agent Orchestrator. Самый жёсткий дисконт даёт не “малость аудитории”, а переупаковка одного и того же ядра в несколько архивов, наличие hardcoded secrets в торговом скрипте, и fork contamination в публичном owner-scope на GitHub[2]. fileciteturn0file0 fileciteturn0file1 fileciteturn0file2 [3]

По live-профилям на 16 апреля 2026 года видно: overandor — 60 repos, jskroby — 118 repos, profitosis — 3 repos. У overandor заметная часть видимого inventory явно помечена как Forked from ...; у jskroby в видимом срезе тоже есть существенный блок форков, а оставшиеся 88 repos в рамках этой сессии не были индивидуально раскрыты по содержимому и потому я держу их только в provisional bucket, а не в fully-underwritten per-repo NAV. У profitosis все 3 репозитория выглядят как оригинальные работы, но с нулевой рыночной тягой по stars/forks на момент просмотра. [4]

Брутально: это портфель boutique R&D / conceptual code / research IP, а не готовый operating software business. Его можно продавать как research package, acquihire-style code asset, demo-led product seed, либо как repo-as-art / compute-backed conceptual artifact для ограниченного круга покупателей. Продавать “как SaaS-компанию” — пока рано.

Периметр и метод

Приоритизация источников была правильной: две Solana/NFT-записки сами по себе оформлены как обзоры, собранные по официальным докам и первичным источникам; это повышает их provenance и коммерческую пригодность как клиентских research deliverables. Торговый Python-скрипт, напротив, сразу теряет стоимость из‑за явного секьюрити-дефекта: в тексте видны plaintext-credentials Gmail OAuth и ключи API для Binance[5], что переводит актив из “buyers can trust” в “buyers must first remediate.” fileciteturn0file0 fileciteturn0file1 fileciteturn0file2

Для GitHub-части я использовал owner-scope и отдельные repo pages. По live-страницам видно не только общий repo count, но и то, какие репозитории помечены как форки. По репо, которые удалось открыть напрямую, есть более сильное доказательство структуры: например, overandor/GPT.research2 имеет 0 stars, 0 forks, 1 commit, Hardhat/Solidity-структуру и README про CartmanBridge; profitosis/fart.foundation имеет 6 commits, набор manpage-like файлов fart.1, fart.2, fart.4, fart.5, fart.7; profitosis/gpt.archive имеет 4 commits, HTML/PDF/chat-artefacts и README “chats.gpt to deploy.” Эти страницы дают достаточную основу для underwritten valuation хотя бы по части inventory. [6]

Оценочная логика простая и жёсткая. Я присваивал каждому активу пять score-компонент: Difficulty, Provenance, Production Readiness, Security Severity, Monetization Potential. Из них строились три оценки: current as-is, realistic buyer value today, polished/productized value. Затем применялся дедуп-дисконт для семей активов, где одна и та же интеллектуальная работа упакована в несколько файлов или архивов. Для repo→art слоя я использовал заданную вами модель:



где RBV — midpoint текущей repo-оценки, D — difficulty score, A — art-transmutation score, P — provenance multiplier. Это не “рыночная цена NFT”, а концептуальный premium для случаев, где репозиторий работает не только как software, но и как compute-backed artifact.

Мастер-реестр

Ниже — MASTER LEDGER SNAPSHOT. Чтобы не создавать ложную точность, я индивидуально underwrite только те items, где есть содержимое или сильный metadata trail. Повторяющиеся мелкие/числовые/клоновые репозитории сведены в baskets, но внутри owner-scope они учтены. Sources для owner inventory и fork filtering — live GitHub pages; sources для research/script — сами загруженные документы и файл со скриптом. fileciteturn0file0 fileciteturn0file1 fileciteturn0file2 [3]

Расшифровка score-пятёрки: D/P/R/S/M = Difficulty / Provenance / Production Readiness / Security Severity / Monetization Potential.

MASTER LEDGER SNAPSHOT — активы, созданные или загруженные в чате

ID

Актив

Класс

Файлы

Происхождение

D/P/R/S/M

Current as-is

Buyer today

Productized

Net after dedupe

U-001

Solana NFT API endpoints research family

research / architecture

Production-ready API endpoints для автоматизированного Solana NFT‑пайплайна.docx; deep-research-report 2.md

upload

8/9/7/1/7

$18k–$40k

$9k–$20k

$30k–$70k

$18k–$40k

U-002

Solana NFT API stack research family

research / architecture

Production-ready API-стек для автоматизированного Solana NFT‑пайплайна на 2026‑04‑15.docx; deep-research-report.md

upload

8/9/7/1/8

$20k–$45k

$10k–$24k

$35k–$80k

$5k–$15k

U-003

TradingView/Binance/Gmail automation script

script / trading automation

Pasted text.txt

upload + earlier pasted code lineage

5/8/3/10/4

$250–$800

$100–$400

$3k–$8k

$250–$800

U-004

Grant Copilot single-file system

AI agent / workflow CLI

grant_copilot_single_file.py

upload

7/8/6/2/7

$5k–$14k

$2.5k–$8k

$18k–$60k

$5k–$14k

U-005

Ollama Agent Orchestrator core demo family

UI / AI agent / demo

ollama-agent-orchestrator-demo.zip; ollama-agent-orchestrator-demo-research.zip; earlier pasted React/Vite app

upload + pasted code

6/8/6/2/7

$4k–$10k

$2k–$6k

$15k–$45k

$4k–$10k

U-006

Ollama submission & investor packaging

research packaging / investor collateral

ollama-agent-orchestrator-investor-demo.zip; ollama-agent-orchestrator-demo-research-submission.zip

upload

3/8/7/1/3

$500–$1.5k

$250–$800

$2k–$6k

$250–$750

MASTER LEDGER SNAPSHOT — GitHub inventory underwritten по overandor

ID

Актив

Класс

Репо / files

Origin

D/P/R/S/M

Current as-is

Buyer today

Productized

Net after dedupe

OV-001

champ-lm

AI agent / research engine

overandor/champ-lm

GitHub live

6/7/3/4/6

$3k–$8k

$1.5k–$4k

$10k–$35k

$3k–$8k

OV-002

nest-js-chatbase-template

backend/UI template

overandor/nest-js-chatbase-template

GitHub live

4/6/4/3/5

$1.5k–$5k

$750–$2.5k

$5k–$18k

$1.5k–$5k

OV-003

GPT.research2

smart contract / DeFi concept

overandor/GPT.research2

GitHub live

4/7/2/5/5

$700–$2k

$300–$1k

$4k–$15k

$700–$2k

OV-004

GPT.research-

research/code concept

overandor/GPT.research-

GitHub live

4/6/2/5/4

$800–$2.4k

$350–$1.2k

$4k–$14k

$800–$2.4k

OV-005

docs

docs

overandor/docs

GitHub live

3/6/4/2/3

$500–$1.5k

$200–$700

$2k–$7k

$500–$1.5k

OV-006

mintlify-docs

docs

overandor/mintlify-docs

GitHub live

3/6/4/2/3

$600–$1.8k

$250–$800

$2.5k–$8k

$600–$1.8k

OV-007

-google-voice-orders

notebook / prototype

overandor/-google-voice-orders

GitHub live

3/6/2/3/3

$400–$1.5k

$150–$600

$2k–$7k

$400–$1.5k

OV-008

flishy

experiment

overandor/flishy

GitHub live

2/5/1/2/2

$200–$700

$100–$300

$1k–$3k

$200–$700

OV-009

ok

experiment

overandor/ok

GitHub live

2/5/2/2/2

$400–$1.2k

$150–$500

$2k–$6k

$400–$1.2k

OV-010

low-signal named utility basket

utilities / prototypes

food; sms; CodeRunnerApp; new-repo; rent

GitHub live

2/5/2/3/3

$600–$2k

$200–$800

$3k–$9k

$600–$2k

OV-011

numeric/orphan original basket

long tail / prototypes

1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,22,23,24,25,28,29,30,31,32,33,34,35,36,37,39,40

GitHub live

2/4/1/3/2

$2k–$7k

$800–$3k

$8k–$22k

$2k–$7k

MASTER LEDGER SNAPSHOT — GitHub inventory underwritten по jskroby

ID

Актив

Класс

Репо / files

Origin

D/P/R/S/M

Current as-is

Buyer today

Productized

Net after dedupe

JS-001

Subquantum

trading / quantitative concept

jskroby/Subquantum

GitHub live

5/6/3/5/6

$2k–$6k

$1k–$3k

$8k–$25k

$2k–$6k

JS-002

AI_Agent_OpenSource_Monetization

AI agent / monetization concept

jskroby/AI_Agent_OpenSource_Monetization

GitHub live

4/6/2/4/6

$1k–$4k

$500–$2k

$6k–$20k

$1k–$4k

JS-003

sim-proxy

backend / proxy

jskroby/sim-proxy

GitHub live

4/6/3/4/5

$800–$2.5k

$300–$1.2k

$4k–$12k

$800–$2.5k

JS-004

SECGPT

AI/security concept

jskroby/SECGPT

GitHub live

4/4/2/5/4

$600–$2k

$250–$900

$3k–$10k

$600–$2k

JS-005

magic-portfolio-for-next-js

frontend / finance UI

jskroby/magic-portfolio-for-next-js

GitHub live

4/5/3/4/5

$700–$2.2k

$300–$1k

$4k–$12k

$700–$2.2k

JS-006

empathic-voice-interface-starter

voice UI starter

jskroby/empathic-voice-interface-starter

GitHub live

4/5/3/4/5

$800–$2.5k

$300–$1.1k

$4k–$14k

$800–$2.5k

JS-007

Nothin1

JS app

jskroby/Nothin1

GitHub live

3/5/3/3/4

$600–$1.8k

$250–$800

$3k–$8k

$600–$1.8k

JS-008

fart-to-midi-dapp

creative app / dapp concept

jskroby/fart-to-midi-dapp

GitHub live

3/5/2/3/4

$500–$1.8k

$200–$700

$3k–$10k

$500–$1.8k

JS-009

creative fart-cluster basket

experiments

fartissimo; farty; farti

GitHub live

2/5/2/3/3

$600–$2k

$200–$800

$3k–$10k

$600–$2k

JS-010

duplicate-variant / low-signal originals basket

long tail / clone cluster

profitosis-; 0v; AI_Agent_OpenSource_Monetization-17c8e; AI_Agent_OpenSource_Monetization-50d8a; ai-agent-open-source-monetization-760be; ai-agent-open-source-monetization; 2de; k; bookish-goggles

GitHub live

2/4/1/3/2

$1.5k–$4.5k

$600–$1.8k

$6k–$18k

$700–$2k

JS-011

unretrieved owner remainder

provisional bucket

remaining 88 repos on profile not individually unfolded in-session

GitHub live, provisional

2/3/1/4/3

$4k–$15k

$1.5k–$6k

$15k–$45k

$2k–$8k

MASTER LEDGER SNAPSHOT — GitHub inventory underwritten по profitosis

ID

Актив

Класс

Репо / files

Origin

D/P/R/S/M

Current as-is

Buyer today

Productized

Net after dedupe

PF-001

nft-appraisal-oracle

NFT / appraisal concept

profitosis/nft-appraisal-oracle

GitHub live

4/7/3/3/7

$1.2k–$3.8k

$600–$1.8k

$8k–$25k

$1.2k–$3.8k

PF-002

fart.foundation

conceptual terminal / art tech

profitosis/fart.foundation

GitHub live

3/7/2/2/3

$500–$2k

$200–$800

$3k–$10k

$500–$2k

PF-003

gpt.archive

archive / HTML artifact

profitosis/gpt.archive

GitHub live

4/7/2/2/5

$800–$3k

$300–$1.2k

$4k–$15k

$800–$3k

Исключённые форки и неавторские репозитории

Эти позиции нулюются в net valuation, потому что публичные страницы сами помечают их как forks. Это особенно важно для overandor: без этого фильтра портфель выглядел бы намного “толще”, чем он есть на самом деле. У jskroby ситуация аналогична в видимом срезе. [7]

Owner

Excluded repo

Upstream

overandor

38

edorim/38

overandor

gptme

gptme/gptme

overandor

Webscout

OEvortex/Webscout

overandor

Joe

butlerx/wetty

overandor

perplexity-ultimate-dashboard

peterparker1718/perplexity-ultimate-dashboard

overandor

userscripts

quoid/userscripts

overandor

chatgpt-exporter

pionxzh/chatgpt-exporter

overandor

gptme-agent-template

gptme/gptme-agent-template

overandor

snap2txt

vorniches/snap2txt

overandor

demo

dependabot/demo

jskroby

czkawka

qarmin/czkawka

jskroby

automa

AutomaApp/automa

jskroby

python-sdk

modelcontextprotocol/python-sdk

jskroby

netlify-mcp

netlify/netlify-mcp

jskroby

text-generation-webui

oobabooga/text-generation-webui

jskroby

dub

dubinc/dub

jskroby

RedisInsight

redis/RedisInsight

jskroby

shark-ai

nod-ai/shark-ai

jskroby

tbpn-twitter-bot

sieve-data/tbpn-twitter-bot

jskroby

surf

e2b-dev/surf

Разбивка по репозиториям и art/NFT-премия

У overandor самая сильная индивидуальная ставка — не форки, а champ-lm; у profitosis программная стоимость ниже, зато у nft-appraisal-oracle, gpt.archive и fart.foundation выше conceptual/art convertibility, потому что сам репозиторий функционирует как артефакт темы “appraisal / archive / terminal-poetry”. У GPT.research2 обратная картина: идея сильнее текущего execution evidence, потому что страница показывает всего один commit и нулевую рыночную тягу. У jskroby visible slice лучше всего держатся Subquantum, AI_Agent_OpenSource_Monetization и sim-proxy, но по ним content-depth weaker, чем хотелось бы для серьёзного M&A. [8]

Per-repo breakdown с RBV→Art uplift

Repo

RBV midpoint

D

A

P-multiplier

Art/NFT-adjusted midpoint

overandor/champ-lm

$5.5k

6

7

1.35x

$14.0k

jskroby/Subquantum

$4.0k

5

6

1.35x

$9.1k

overandor/nest-js-chatbase-template

$3.25k

4

5

1.25x

$6.0k

profitosis/nft-appraisal-oracle

$2.5k

4

8

1.40x

$6.0k

jskroby/AI_Agent_OpenSource_Monetization

$2.5k

4

6

1.30x

$5.1k

profitosis/gpt.archive

$1.9k

4

8

1.35x

$4.4k

overandor/GPT.research-

$1.6k

4

6

1.30x

$3.2k

jskroby/sim-proxy

$1.65k

4

5

1.25x

$3.1k

overandor/GPT.research2

$1.35k

4

7

1.30x

$2.9k

profitosis/fart.foundation

$1.25k

3

8

1.35x

$2.7k

jskroby/SECGPT

$1.3k

4

6

1.10x

$2.2k

Roll-up по owner scope

Owner / family

Repo count on profile

Observed forks excluded

Underwritten original inventory

Unresolved remainder

Net buyer value

Net productized value

overandor

60

10

50

0

$4.75k–$15.4k

$43.5k–$144k

jskroby

118

10 observed

20 observed originals + baskets

88 repos

$4.3k–$15.3k

$46.5k–$147k

profitosis

3

0

3

0

$1.1k–$3.8k

$15k–$50k

Динамика стоимости и связь активов

Поскольку prior state по вашему условию считается пустым, вся текущая net valuation одновременно является delta from zero. Это хорошо для storytelling, но плохо для дисциплины: инвестору важно помнить, что часть этой дельты создаётся не новыми cash-generating assets, а просто сборкой и упаковкой уже существующих работ в один ledger.

Портфельные итоги

Метрика

До дедупа

После дедупа

Gross current as-is

$74.05k–$197.5k

$56k–$157.25k

Gross realistic buyer value

$35.1k–$97.7k

$26.35k–$77.25k

Gross productized value

$220.5k–$647k

$180.5k–$550k

Изменение от предыдущего состояния

Метрика

Prior state

Current

Delta

Net current as-is

$0

$56k–$157.25k

+$56k–$157.25k

Net realistic buyer value

$0

$26.35k–$77.25k

+$26.35k–$77.25k

Net productized value

$0

$180.5k–$550k

+$180.5k–$550k

Top-10 вкладчиков в стоимость портфеля

Rank

Asset

Midpoint of net buyer value

1

U-001 Solana NFT API endpoints research family

$14.5k

2

U-002 Solana NFT API stack research family

$5.25k

3

U-004 Grant Copilot single-file system

$5.25k

4

U-005 Ollama Agent Orchestrator core demo family

$4.0k

5

OV-001 champ-lm

$2.75k

6

JS-001 Subquantum

$2.0k

7

OV-011 numeric/orphan original basket

$1.9k

8

JS-011 unretrieved remainder bucket

$1.875k

9

OV-002 nest-js-chatbase-template

$1.625k

10

JS-002 AI_Agent_OpenSource_Monetization

$1.25k

Ключевые драйверы стоимости

Driver

Почему это важно

Исследовательские Solana/NFT-записки

Это самое “продаваемое” сегодня: они ближе всего к billable client research и already framed as primary-source syntheses.

Grant Copilot

Один файл, локальный inference path, тесты, аудит и экспортная логика делают актив ближе к usable internal tooling, чем к просто “кодовой заметке”.

Ollama demo family

Хороший demo-packaging для pre-seed / investor narrative; не operational, но именно поэтому безопаснее для показа.

Conceptual repo-to-art layer

У profitosis и части jskroby/overandor есть не только software value, но и curator-friendly conceptual framing.

Главные leaks стоимости

Leak

Эффект

Hardcoded secrets in trading script

Немедленный security discount и trust discount.

Fork contamination

Без ручной очистки owner-scope визуально переоценён.

Дубликаты и близнецы

Несколько zip/doc variants почти не добавляют нового NAV.

Opaque repo naming

Числовые и однословные repo names режут discoverability и buyer confidence.

Отсутствие traction evidence

Нулевые stars/forks/релизы/usage metrics ограничивают buyer multiple.

Неполное раскрытие хвоста jskroby

88 repo остаются provisional, а не cleanly underwritten.

Packaging hygiene

Локально видно, что один из demo-архивов раздут включёнными node_modules, что для покупателя выглядит как неподготовленный asset.

Mermaid timeline

timeline
    title Этапы оценки
    2026-04-16 : Зафиксированы uploads и pasted code
    2026-04-16 : Нормализованы семейства активов
    2026-04-16 : Проверены owner-scoped GitHub profiles
    2026-04-16 : Форки помечены и исключены из net ledger
    2026-04-16 : Присвоены D/P/R/S/M scorecards
    2026-04-16 : Посчитаны current, buyer, productized ranges
    2026-04-16 : Применён repo→art uplift для применимых репозиториев
    2026-04-16 : Собраны portfolio totals и top value contributors

Mermaid ER-style chart

erDiagram
    CHAT ||--o{ ASSET : contains
    ASSET ||--o{ FILE : represented_by
    ASSET ||--o{ REPO : may_map_to
    OWNER ||--o{ REPO : owns

    CHAT {
        string chat_id
        string origin_type
    }

    ASSET {
        string asset_id
        string class
        string valuation_status
    }

    FILE {
        string filename
        string upload_family
    }

    OWNER {
        string owner_handle
        string scope_status
    }

    REPO {
        string repo_name
        string fork_status
    }

Жёсткий вывод

Если говорить без маркетинговой ваты, картина такая.

Первое. Самая ликвидная часть портфеля — это исследование и tooling, а не GitHub как таковой. Две Solana/NFT-записки похожи на то, что реально покупают консалтинг-клиенты или founder teams, когда им нужен fast architectural certainty. grant_copilot_single_file.py тоже живой актив: он уже ближе к внутреннему продукту, чем к просто демо-коду.

Второе. Публичные GitHub-портфели overandor и jskroby выглядят широко, но после фильтра “не считать форки” и после вопроса “что именно из этого покупатель сможет immediately reuse?” стоимость резко сжимается. У overandor это особенно заметно: видимая страница показывает одновременно и оригинальные эксперименты, и существенный блок форков вроде gptme, Webscout, Joe, userscripts, chatgpt-exporter; после их вычитания value концентрируется в champ-lm, nest-js-chatbase-template, двух GPT.research* и длинном слабом хвосте. [9]

Третье. У profitosis программная ценность небольшая, но тематическая когерентность сильнее: nft-appraisal-oracle, fart.foundation, gpt.archive образуют довольно редкий для GitHub треугольник — appraisal/oracle, terminal-manpage art-tech и archive object. Это именно тот случай, где repo→art модель уместна: как software это modest inventory, как conceptual compute-backed artifacts — уже интереснее. Страницы репозиториев при этом показывают почти нулевую traction-базу, так что premium здесь кураторский, а не массовый. [10]

Четвёртое. Главный blocker не “недостаток идей”, а неупакованность доказательств. Чтобы переместиться из диапазона $26k–$77k realistic buyer value к верхней части $180k–$550k productized value, нужно сделать четыре вещи: 1. убрать plaintext secrets и пройти минимальную security hygiene; 2. сократить дубликаты и оставить один canonical artifact per family; 3. дать понятные README/demo/install/results для strongest original repos; 4. для GitHub long tail — либо архивировать мусор, либо переименовать и собрать thesis-driven collections.

Пятое. Инвесторский hard truth: сегодня это не portfolio of companies. Это portfolio of intellectual work units. У него есть цена. Но эта цена пока возникает не из revenue, не из MAU, не из defensible moat, а из replacement cost + research density + packaging potential + conceptual premium. Пока вы не покажете usage, customer pull или хотя бы clean benchmarked proof of capability, рынок будет покупать это как asset strip, а не как полноценный operating business.



[1] [2] [3] [4] [7] https://github.com/overandor?tab=repositories

https://github.com/overandor?tab=repositories

[5] [10] https://github.com/profitosis?tab=repositories

https://github.com/profitosis?tab=repositories

[6] [8] https://github.com/overandor/GPT.research2

https://github.com/overandor/GPT.research2

[9] https://github.com/overandor?page=2&tab=repositories

https://github.com/overandor?page=2&tab=repositories

#### ChatGPT:
Новый загруженный DOCX это подтверждает: в нём прямо перечислены `deep-research-report.md` и `deep-research-report 2.md` как отдельные артефакты вашего аккаунта, связанные с Solana/NFT research family.

Значит, подтверждённый список сейчас такой:

1. `deep-research-report.md`
2. `deep-research-report 2.md`
3. `Долларовая оценка активов и репозиториев из чата.docx` - содержит ссылки на оба этих файла.
4. `MyActivity.html` - содержит упоминания Deep Research / Deep Research agent в истории активности.

Самое важное: теперь уже не просто “есть упоминание Deep Research”, а именно есть текстовое подтверждение названий двух файлов-результатов глубокого исследования в вашем аккаунте.

Могу следующим сообщением собрать это в аккуратный реестр: `имя файла | тип | откуда подтверждено | насколько это прямое совпадение`.


#### You:


#### Plugin (file_search):
Make sure to include fileciteturn3file0 in your response to cite this file, or to surface it as a link.
Долларовая оценка активов и репозиториев из чата

Резюме для инвестора

После дедупликации версий, вычитания форков и дисконта за непроверяемый хвост инвентаря, мой рабочий диапазон для портфеля выглядит так: gross as-is — $74k–$198k, net realistic buyer value today — $26.35k–$77.25k, net productized portfolio value — $180.5k–$550k. Самая ценная часть портфеля — не длинный хвост публичных репозиториев, а две исследовательские записки по production-ready API для NFT-пайплайна на Solana[1], затем single-file-система Grant Copilot, затем семейство безопасного demo/UI для Ollama Agent Orchestrator. Самый жёсткий дисконт даёт не “малость аудитории”, а переупаковка одного и того же ядра в несколько архивов, наличие hardcoded secrets в торговом скрипте, и fork contamination в публичном owner-scope на GitHub[2]. fileciteturn0file0 fileciteturn0file1 fileciteturn0file2 [3]

По live-профилям на 16 апреля 2026 года видно: overandor — 60 repos, jskroby — 118 repos, profitosis — 3 repos. У overandor заметная часть видимого inventory явно помечена как Forked from ...; у jskroby в видимом срезе тоже есть существенный блок форков, а оставшиеся 88 repos в рамках этой сессии не были индивидуально раскрыты по содержимому и потому я держу их только в provisional bucket, а не в fully-underwritten per-repo NAV. У profitosis все 3 репозитория выглядят как оригинальные работы, но с нулевой рыночной тягой по stars/forks на момент просмотра. [4]

Брутально: это портфель boutique R&D / conceptual code / research IP, а не готовый operating software business. Его можно продавать как research package, acquihire-style code asset, demo-led product seed, либо как repo-as-art / compute-backed conceptual artifact для ограниченного круга покупателей. Продавать “как SaaS-компанию” — пока рано.

Периметр и метод

Приоритизация источников была правильной: две Solana/NFT-записки сами по себе оформлены как обзоры, собранные по официальным докам и первичным источникам; это повышает их provenance и коммерческую пригодность как клиентских research deliverables. Торговый Python-скрипт, напротив, сразу теряет стоимость из‑за явного секьюрити-дефекта: в тексте видны plaintext-credentials Gmail OAuth и ключи API для Binance[5], что переводит актив из “buyers can trust” в “buyers must first remediate.” fileciteturn0file0 fileciteturn0file1 fileciteturn0file2

Для GitHub-части я использовал owner-scope и отдельные repo pages. По live-страницам видно не только общий repo count, но и то, какие репозитории помечены как форки. По репо, которые удалось открыть напрямую, есть более сильное доказательство структуры: например, overandor/GPT.research2 имеет 0 stars, 0 forks, 1 commit, Hardhat/Solidity-структуру и README про CartmanBridge; profitosis/fart.foundation имеет 6 commits, набор manpage-like файлов fart.1, fart.2, fart.4, fart.5, fart.7; profitosis/gpt.archive имеет 4 commits, HTML/PDF/chat-artefacts и README “chats.gpt to deploy.” Эти страницы дают достаточную основу для underwritten valuation хотя бы по части inventory. [6]

Оценочная логика простая и жёсткая. Я присваивал каждому активу пять score-компонент: Difficulty, Provenance, Production Readiness, Security Severity, Monetization Potential. Из них строились три оценки: current as-is, realistic buyer value today, polished/productized value. Затем применялся дедуп-дисконт для семей активов, где одна и та же интеллектуальная работа упакована в несколько файлов или архивов. Для repo→art слоя я использовал заданную вами модель:



где RBV — midpoint текущей repo-оценки, D — difficulty score, A — art-transmutation score, P — provenance multiplier. Это не “рыночная цена NFT”, а концептуальный premium для случаев, где репозиторий работает не только как software, но и как compute-backed artifact.

Мастер-реестр

Ниже — MASTER LEDGER SNAPSHOT. Чтобы не создавать ложную точность, я индивидуально underwrite только те items, где есть содержимое или сильный metadata trail. Повторяющиеся мелкие/числовые/клоновые репозитории сведены в baskets, но внутри owner-scope они учтены. Sources для owner inventory и fork filtering — live GitHub pages; sources для research/script — сами загруженные документы и файл со скриптом. fileciteturn0file0 fileciteturn0file1 fileciteturn0file2 [3]

Расшифровка score-пятёрки: D/P/R/S/M = Difficulty / Provenance / Production Readiness / Security Severity / Monetization Potential.

MASTER LEDGER SNAPSHOT — активы, созданные или загруженные в чате

ID

Актив

Класс

Файлы

Происхождение

D/P/R/S/M

Current as-is

Buyer today

Productized

Net after dedupe

U-001

Solana NFT API endpoints research family

research / architecture

Production-ready API endpoints для автоматизированного Solana NFT‑пайплайна.docx; deep-research-report 2.md

upload

8/9/7/1/7

$18k–$40k

$9k–$20k

$30k–$70k

$18k–$40k

U-002

Solana NFT API stack research family

research / architecture

Production-ready API-стек для автоматизированного Solana NFT‑пайплайна на 2026‑04‑15.docx; deep-research-report.md

upload

8/9/7/1/8

$20k–$45k

$10k–$24k

$35k–$80k

$5k–$15k

U-003

TradingView/Binance/Gmail automation script

script / trading automation

Pasted text.txt

upload + earlier pasted code lineage

5/8/3/10/4

$250–$800

$100–$400

$3k–$8k

$250–$800

U-004

Grant Copilot single-file system

AI agent / workflow CLI

grant_copilot_single_file.py

upload

7/8/6/2/7

$5k–$14k

$2.5k–$8k

$18k–$60k

$5k–$14k

U-005

Ollama Agent Orchestrator core demo family

UI / AI agent / demo

ollama-agent-orchestrator-demo.zip; ollama-agent-orchestrator-demo-research.zip; earlier pasted React/Vite app

upload + pasted code

6/8/6/2/7

$4k–$10k

$2k–$6k

$15k–$45k

$4k–$10k

U-006

Ollama submission & investor packaging

research packaging / investor collateral

ollama-agent-orchestrator-investor-demo.zip; ollama-agent-orchestrator-demo-research-submission.zip

upload

3/8/7/1/3

$500–$1.5k

$250–$800

$2k–$6k

$250–$750

MASTER LEDGER SNAPSHOT — GitHub inventory underwritten по overandor

ID

Актив

Класс

Репо / files

Origin

D/P/R/S/M

Current as-is

Buyer today

Productized

Net after dedupe

OV-001

champ-lm

AI agent / research engine

overandor/champ-lm

GitHub live

6/7/3/4/6

$3k–$8k

$1.5k–$4k

$10k–$35k

$3k–$8k

OV-002

nest-js-chatbase-template

backend/UI template

overandor/nest-js-chatbase-template

GitHub live

4/6/4/3/5

$1.5k–$5k

$750–$2.5k

$5k–$18k

$1.5k–$5k

OV-003

GPT.research2

smart contract / DeFi concept

overandor/GPT.research2

GitHub live

4/7/2/5/5

$700–$2k

$300–$1k

$4k–$15k

$700–$2k

OV-004

GPT.research-

research/code concept

overandor/GPT.research-

GitHub live

4/6/2/5/4

$800–$2.4k

$350–$1.2k

$4k–$14k

$800–$2.4k

OV-005

docs

docs

overandor/docs

GitHub live

3/6/4/2/3

$500–$1.5k

$200–$700

$2k–$7k

$500–$1.5k

OV-006

mintlify-docs

docs

overandor/mintlify-docs

GitHub live

3/6/4/2/3

$600–$1.8k

$250–$800

$2.5k–$8k

$600–$1.8k

OV-007

-google-voice-orders

notebook / prototype

overandor/-google-voice-orders

GitHub live

3/6/2/3/3

$400–$1.5k

$150–$600

$2k–$7k

$400–$1.5k

OV-008

flishy

experiment

overandor/flishy

GitHub live

2/5/1/2/2

$200–$700

$100–$300

$1k–$3k

$200–$700

OV-009

ok

experiment

overandor/ok

GitHub live

2/5/2/2/2

$400–$1.2k

$150–$500

$2k–$6k

$400–$1.2k

OV-010

low-signal named utility basket

utilities / prototypes

food; sms; CodeRunnerApp; new-repo; rent

GitHub live

2/5/2/3/3

$600–$2k

$200–$800

$3k–$9k

$600–$2k

OV-011

numeric/orphan original basket

long tail / prototypes

1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,22,23,24,25,28,29,30,31,32,33,34,35,36,37,39,40

GitHub live

2/4/1/3/2

$2k–$7k

$800–$3k

$8k–$22k

$2k–$7k

MASTER LEDGER SNAPSHOT — GitHub inventory underwritten по jskroby

ID

Актив

Класс

Репо / files

Origin

D/P/R/S/M

Current as-is

Buyer today

Productized

Net after dedupe

JS-001

Subquantum

trading / quantitative concept

jskroby/Subquantum

GitHub live

5/6/3/5/6

$2k–$6k

$1k–$3k

$8k–$25k

$2k–$6k

JS-002

AI_Agent_OpenSource_Monetization

AI agent / monetization concept

jskroby/AI_Agent_OpenSource_Monetization

GitHub live

4/6/2/4/6

$1k–$4k

$500–$2k

$6k–$20k

$1k–$4k

JS-003

sim-proxy

backend / proxy

jskroby/sim-proxy

GitHub live

4/6/3/4/5

$800–$2.5k

$300–$1.2k

$4k–$12k

$800–$2.5k

JS-004

SECGPT

AI/security concept

jskroby/SECGPT

GitHub live

4/4/2/5/4

$600–$2k

$250–$900

$3k–$10k

$600–$2k

JS-005

magic-portfolio-for-next-js

frontend / finance UI

jskroby/magic-portfolio-for-next-js

GitHub live

4/5/3/4/5

$700–$2.2k

$300–$1k

$4k–$12k

$700–$2.2k

JS-006

empathic-voice-interface-starter

voice UI starter

jskroby/empathic-voice-interface-starter

GitHub live

4/5/3/4/5

$800–$2.5k

$300–$1.1k

$4k–$14k

$800–$2.5k

JS-007

Nothin1

JS app

jskroby/Nothin1

GitHub live

3/5/3/3/4

$600–$1.8k

$250–$800

$3k–$8k

$600–$1.8k

JS-008

fart-to-midi-dapp

creative app / dapp concept

jskroby/fart-to-midi-dapp

GitHub live

3/5/2/3/4

$500–$1.8k

$200–$700

$3k–$10k

$500–$1.8k

JS-009

creative fart-cluster basket

experiments

fartissimo; farty; farti

GitHub live

2/5/2/3/3

$600–$2k

$200–$800

$3k–$10k

$600–$2k

JS-010

duplicate-variant / low-signal originals basket

long tail / clone cluster

profitosis-; 0v; AI_Agent_OpenSource_Monetization-17c8e; AI_Agent_OpenSource_Monetization-50d8a; ai-agent-open-source-monetization-760be; ai-agent-open-source-monetization; 2de; k; bookish-goggles

GitHub live

2/4/1/3/2

$1.5k–$4.5k

$600–$1.8k

$6k–$18k

$700–$2k

JS-011

unretrieved owner remainder

provisional bucket

remaining 88 repos on profile not individually unfolded in-session

GitHub live, provisional

2/3/1/4/3

$4k–$15k

$1.5k–$6k

$15k–$45k

$2k–$8k

MASTER LEDGER SNAPSHOT — GitHub inventory underwritten по profitosis

ID

Актив

Класс

Репо / files

Origin

D/P/R/S/M

Current as-is

Buyer today

Productized

Net after dedupe

PF-001

nft-appraisal-oracle

NFT / appraisal concept

profitosis/nft-appraisal-oracle

GitHub live

4/7/3/3/7

$1.2k–$3.8k

$600–$1.8k

$8k–$25k

$1.2k–$3.8k

PF-002

fart.foundation

conceptual terminal / art tech

profitosis/fart.foundation

GitHub live

3/7/2/2/3

$500–$2k

$200–$800

$3k–$10k

$500–$2k

PF-003

gpt.archive

archive / HTML artifact

profitosis/gpt.archive

GitHub live

4/7/2/2/5

$800–$3k

$300–$1.2k

$4k–$15k

$800–$3k

Исключённые форки и неавторские репозитории

Эти позиции нулюются в net valuation, потому что публичные страницы сами помечают их как forks. Это особенно важно для overandor: без этого фильтра портфель выглядел бы намного “толще”, чем он есть на самом деле. У jskroby ситуация аналогична в видимом срезе. [7]

Owner

Excluded repo

Upstream

overandor

38

edorim/38

overandor

gptme

gptme/gptme

overandor

Webscout

OEvortex/Webscout

overandor

Joe

butlerx/wetty

overandor

perplexity-ultimate-dashboard

peterparker1718/perplexity-ultimate-dashboard

overandor

userscripts

quoid/userscripts

overandor

chatgpt-exporter

pionxzh/chatgpt-exporter

overandor

gptme-agent-template

gptme/gptme-agent-template

overandor

snap2txt

vorniches/snap2txt

overandor

demo

dependabot/demo

jskroby

czkawka

qarmin/czkawka

jskroby

automa

AutomaApp/automa

jskroby

python-sdk

modelcontextprotocol/python-sdk

jskroby

netlify-mcp

netlify/netlify-mcp

jskroby

text-generation-webui

oobabooga/text-generation-webui

jskroby

dub

dubinc/dub

jskroby

RedisInsight

redis/RedisInsight

jskroby

shark-ai

nod-ai/shark-ai

jskroby

tbpn-twitter-bot

sieve-data/tbpn-twitter-bot

jskroby

surf

e2b-dev/surf

Разбивка по репозиториям и art/NFT-премия

У overandor самая сильная индивидуальная ставка — не форки, а champ-lm; у profitosis программная стоимость ниже, зато у nft-appraisal-oracle, gpt.archive и fart.foundation выше conceptual/art convertibility, потому что сам репозиторий функционирует как артефакт темы “appraisal / archive / terminal-poetry”. У GPT.research2 обратная картина: идея сильнее текущего execution evidence, потому что страница показывает всего один commit и нулевую рыночную тягу. У jskroby visible slice лучше всего держатся Subquantum, AI_Agent_OpenSource_Monetization и sim-proxy, но по ним content-depth weaker, чем хотелось бы для серьёзного M&A. [8]

Per-repo breakdown с RBV→Art uplift

Repo

RBV midpoint

D

A

P-multiplier

Art/NFT-adjusted midpoint

overandor/champ-lm

$5.5k

6

7

1.35x

$14.0k

jskroby/Subquantum

$4.0k

5

6

1.35x

$9.1k

overandor/nest-js-chatbase-template

$3.25k

4

5

1.25x

$6.0k

profitosis/nft-appraisal-oracle

$2.5k

4

8

1.40x

$6.0k

jskroby/AI_Agent_OpenSource_Monetization

$2.5k

4

6

1.30x

$5.1k

profitosis/gpt.archive

$1.9k

4

8

1.35x

$4.4k

overandor/GPT.research-

$1.6k

4

6

1.30x

$3.2k

jskroby/sim-proxy

$1.65k

4

5

1.25x

$3.1k

overandor/GPT.research2

$1.35k

4

7

1.30x

$2.9k

profitosis/fart.foundation

$1.25k

3

8

1.35x

$2.7k

jskroby/SECGPT

$1.3k

4

6

1.10x

$2.2k

Roll-up по owner scope

Owner / family

Repo count on profile

Observed forks excluded

Underwritten original inventory

Unresolved remainder

Net buyer value

Net productized value

overandor

60

10

50

0

$4.75k–$15.4k

$43.5k–$144k

jskroby

118

10 observed

20 observed originals + baskets

88 repos

$4.3k–$15.3k

$46.5k–$147k

profitosis

3

0

3

0

$1.1k–$3.8k

$15k–$50k

Динамика стоимости и связь активов

Поскольку prior state по вашему условию считается пустым, вся текущая net valuation одновременно является delta from zero. Это хорошо для storytelling, но плохо для дисциплины: инвестору важно помнить, что часть этой дельты создаётся не новыми cash-generating assets, а просто сборкой и упаковкой уже существующих работ в один ledger.

Портфельные итоги

Метрика

До дедупа

После дедупа

Gross current as-is

$74.05k–$197.5k

$56k–$157.25k

Gross realistic buyer value

$35.1k–$97.7k

$26.35k–$77.25k

Gross productized value

$220.5k–$647k

$180.5k–$550k

Изменение от предыдущего состояния

Метрика

Prior state

Current

Delta

Net current as-is

$0

$56k–$157.25k

+$56k–$157.25k

Net realistic buyer value

$0

$26.35k–$77.25k

+$26.35k–$77.25k

Net productized value

$0

$180.5k–$550k

+$180.5k–$550k

Top-10 вкладчиков в стоимость портфеля

Rank

Asset

Midpoint of net buyer value

1

U-001 Solana NFT API endpoints research family

$14.5k

2

U-002 Solana NFT API stack research family

$5.25k

3

U-004 Grant Copilot single-file system

$5.25k

4

U-005 Ollama Agent Orchestrator core demo family

$4.0k

5

OV-001 champ-lm

$2.75k

6

JS-001 Subquantum

$2.0k

7

OV-011 numeric/orphan original basket

$1.9k

8

JS-011 unretrieved remainder bucket

$1.875k

9

OV-002 nest-js-chatbase-template

$1.625k

10

JS-002 AI_Agent_OpenSource_Monetization

$1.25k

Ключевые драйверы стоимости

Driver

Почему это важно

Исследовательские Solana/NFT-записки

Это самое “продаваемое” сегодня: они ближе всего к billable client research и already framed as primary-source syntheses.

Grant Copilot

Один файл, локальный inference path, тесты, аудит и экспортная логика делают актив ближе к usable internal tooling, чем к просто “кодовой заметке”.

Ollama demo family

Хороший demo-packaging для pre-seed / investor narrative; не operational, но именно поэтому безопаснее для показа.

Conceptual repo-to-art layer

У profitosis и части jskroby/overandor есть не только software value, но и curator-friendly conceptual framing.

Главные leaks стоимости

Leak

Эффект

Hardcoded secrets in trading script

Немедленный security discount и trust discount.

Fork contamination

Без ручной очистки owner-scope визуально переоценён.

Дубликаты и близнецы

Несколько zip/doc variants почти не добавляют нового NAV.

Opaque repo naming

Числовые и однословные repo names режут discoverability и buyer confidence.

Отсутствие traction evidence

Нулевые stars/forks/релизы/usage metrics ограничивают buyer multiple.

Неполное раскрытие хвоста jskroby

88 repo остаются provisional, а не cleanly underwritten.

Packaging hygiene

Локально видно, что один из demo-архивов раздут включёнными node_modules, что для покупателя выглядит как неподготовленный asset.

Mermaid timeline

timeline
    title Этапы оценки
    2026-04-16 : Зафиксированы uploads и pasted code
    2026-04-16 : Нормализованы семейства активов
    2026-04-16 : Проверены owner-scoped GitHub profiles
    2026-04-16 : Форки помечены и исключены из net ledger
    2026-04-16 : Присвоены D/P/R/S/M scorecards
    2026-04-16 : Посчитаны current, buyer, productized ranges
    2026-04-16 : Применён repo→art uplift для применимых репозиториев
    2026-04-16 : Собраны portfolio totals и top value contributors

Mermaid ER-style chart

erDiagram
    CHAT ||--o{ ASSET : contains
    ASSET ||--o{ FILE : represented_by
    ASSET ||--o{ REPO : may_map_to
    OWNER ||--o{ REPO : owns

    CHAT {
        string chat_id
        string origin_type
    }

    ASSET {
        string asset_id
        string class
        string valuation_status
    }

    FILE {
        string filename
        string upload_family
    }

    OWNER {
        string owner_handle
        string scope_status
    }

    REPO {
        string repo_name
        string fork_status
    }

Жёсткий вывод

Если говорить без маркетинговой ваты, картина такая.

Первое. Самая ликвидная часть портфеля — это исследование и tooling, а не GitHub как таковой. Две Solana/NFT-записки похожи на то, что реально покупают консалтинг-клиенты или founder teams, когда им нужен fast architectural certainty. grant_copilot_single_file.py тоже живой актив: он уже ближе к внутреннему продукту, чем к просто демо-коду.

Второе. Публичные GitHub-портфели overandor и jskroby выглядят широко, но после фильтра “не считать форки” и после вопроса “что именно из этого покупатель сможет immediately reuse?” стоимость резко сжимается. У overandor это особенно заметно: видимая страница показывает одновременно и оригинальные эксперименты, и существенный блок форков вроде gptme, Webscout, Joe, userscripts, chatgpt-exporter; после их вычитания value концентрируется в champ-lm, nest-js-chatbase-template, двух GPT.research* и длинном слабом хвосте. [9]

Третье. У profitosis программная ценность небольшая, но тематическая когерентность сильнее: nft-appraisal-oracle, fart.foundation, gpt.archive образуют довольно редкий для GitHub треугольник — appraisal/oracle, terminal-manpage art-tech и archive object. Это именно тот случай, где repo→art модель уместна: как software это modest inventory, как conceptual compute-backed artifacts — уже интереснее. Страницы репозиториев при этом показывают почти нулевую traction-базу, так что premium здесь кураторский, а не массовый. [10]

Четвёртое. Главный blocker не “недостаток идей”, а неупакованность доказательств. Чтобы переместиться из диапазона $26k–$77k realistic buyer value к верхней части $180k–$550k productized value, нужно сделать четыре вещи: 1. убрать plaintext secrets и пройти минимальную security hygiene; 2. сократить дубликаты и оставить один canonical artifact per family; 3. дать понятные README/demo/install/results для strongest original repos; 4. для GitHub long tail — либо архивировать мусор, либо переименовать и собрать thesis-driven collections.

Пятое. Инвесторский hard truth: сегодня это не portfolio of companies. Это portfolio of intellectual work units. У него есть цена. Но эта цена пока возникает не из revenue, не из MAU, не из defensible moat, а из replacement cost + research density + packaging potential + conceptual premium. Пока вы не покажете usage, customer pull или хотя бы clean benchmarked proof of capability, рынок будет покупать это как asset strip, а не как полноценный operating business.



[1] [2] [3] [4] [7] https://github.com/overandor?tab=repositories

https://github.com/overandor?tab=repositories

[5] [10] https://github.com/profitosis?tab=repositories

https://github.com/profitosis?tab=repositories

[6] [8] https://github.com/overandor/GPT.research2

https://github.com/overandor/GPT.research2

[9] https://github.com/overandor?page=2&tab=repositories

https://github.com/overandor?page=2&tab=repositories

#### Plugin (file_search):
Make sure to include fileciteturn3file1 in your response to cite this file, or to surface it as a link.
Долларовая оценка активов и репозиториев из чата

Резюме для инвестора

После дедупликации версий, вычитания форков и дисконта за непроверяемый хвост инвентаря, мой рабочий диапазон для портфеля выглядит так: gross as-is — $74k–$198k, net realistic buyer value today — $26.35k–$77.25k, net productized portfolio value — $180.5k–$550k. Самая ценная часть портфеля — не длинный хвост публичных репозиториев, а две исследовательские записки по production-ready API для NFT-пайплайна на Solana[1], затем single-file-система Grant Copilot, затем семейство безопасного demo/UI для Ollama Agent Orchestrator. Самый жёсткий дисконт даёт не “малость аудитории”, а переупаковка одного и того же ядра в несколько архивов, наличие hardcoded secrets в торговом скрипте, и fork contamination в публичном owner-scope на GitHub[2]. fileciteturn0file0 fileciteturn0file1 fileciteturn0file2 [3]

По live-профилям на 16 апреля 2026 года видно: overandor — 60 repos, jskroby — 118 repos, profitosis — 3 repos. У overandor заметная часть видимого inventory явно помечена как Forked from ...; у jskroby в видимом срезе тоже есть существенный блок форков, а оставшиеся 88 repos в рамках этой сессии не были индивидуально раскрыты по содержимому и потому я держу их только в provisional bucket, а не в fully-underwritten per-repo NAV. У profitosis все 3 репозитория выглядят как оригинальные работы, но с нулевой рыночной тягой по stars/forks на момент просмотра. [4]

Брутально: это портфель boutique R&D / conceptual code / research IP, а не готовый operating software business. Его можно продавать как research package, acquihire-style code asset, demo-led product seed, либо как repo-as-art / compute-backed conceptual artifact для ограниченного круга покупателей. Продавать “как SaaS-компанию” — пока рано.

Периметр и метод

Приоритизация источников была правильной: две Solana/NFT-записки сами по себе оформлены как обзоры, собранные по официальным докам и первичным источникам; это повышает их provenance и коммерческую пригодность как клиентских research deliverables. Торговый Python-скрипт, напротив, сразу теряет стоимость из‑за явного секьюрити-дефекта: в тексте видны plaintext-credentials Gmail OAuth и ключи API для Binance[5], что переводит актив из “buyers can trust” в “buyers must first remediate.” fileciteturn0file0 fileciteturn0file1 fileciteturn0file2

Для GitHub-части я использовал owner-scope и отдельные repo pages. По live-страницам видно не только общий repo count, но и то, какие репозитории помечены как форки. По репо, которые удалось открыть напрямую, есть более сильное доказательство структуры: например, overandor/GPT.research2 имеет 0 stars, 0 forks, 1 commit, Hardhat/Solidity-структуру и README про CartmanBridge; profitosis/fart.foundation имеет 6 commits, набор manpage-like файлов fart.1, fart.2, fart.4, fart.5, fart.7; profitosis/gpt.archive имеет 4 commits, HTML/PDF/chat-artefacts и README “chats.gpt to deploy.” Эти страницы дают достаточную основу для underwritten valuation хотя бы по части inventory. [6]

Оценочная логика простая и жёсткая. Я присваивал каждому активу пять score-компонент: Difficulty, Provenance, Production Readiness, Security Severity, Monetization Potential. Из них строились три оценки: current as-is, realistic buyer value today, polished/productized value. Затем применялся дедуп-дисконт для семей активов, где одна и та же интеллектуальная работа упакована в несколько файлов или архивов. Для repo→art слоя я использовал заданную вами модель:



где RBV — midpoint текущей repo-оценки, D — difficulty score, A — art-transmutation score, P — provenance multiplier. Это не “рыночная цена NFT”, а концептуальный premium для случаев, где репозиторий работает не только как software, но и как compute-backed artifact.

Мастер-реестр

Ниже — MASTER LEDGER SNAPSHOT. Чтобы не создавать ложную точность, я индивидуально underwrite только те items, где есть содержимое или сильный metadata trail. Повторяющиеся мелкие/числовые/клоновые репозитории сведены в baskets, но внутри owner-scope они учтены. Sources для owner inventory и fork filtering — live GitHub pages; sources для research/script — сами загруженные документы и файл со скриптом. fileciteturn0file0 fileciteturn0file1 fileciteturn0file2 [3]

Расшифровка score-пятёрки: D/P/R/S/M = Difficulty / Provenance / Production Readiness / Security Severity / Monetization Potential.

MASTER LEDGER SNAPSHOT — активы, созданные или загруженные в чате

ID

Актив

Класс

Файлы

Происхождение

D/P/R/S/M

Current as-is

Buyer today

Productized

Net after dedupe

U-001

Solana NFT API endpoints research family

research / architecture

Production-ready API endpoints для автоматизированного Solana NFT‑пайплайна.docx; deep-research-report 2.md

upload

8/9/7/1/7

$18k–$40k

$9k–$20k

$30k–$70k

$18k–$40k

U-002

Solana NFT API stack research family

research / architecture

Production-ready API-стек для автоматизированного Solana NFT‑пайплайна на 2026‑04‑15.docx; deep-research-report.md

upload

8/9/7/1/8

$20k–$45k

$10k–$24k

$35k–$80k

$5k–$15k

U-003

TradingView/Binance/Gmail automation script

script / trading automation

Pasted text.txt

upload + earlier pasted code lineage

5/8/3/10/4

$250–$800

$100–$400

$3k–$8k

$250–$800

U-004

Grant Copilot single-file system

AI agent / workflow CLI

grant_copilot_single_file.py

upload

7/8/6/2/7

$5k–$14k

$2.5k–$8k

$18k–$60k

$5k–$14k

U-005

Ollama Agent Orchestrator core demo family

UI / AI agent / demo

ollama-agent-orchestrator-demo.zip; ollama-agent-orchestrator-demo-research.zip; earlier pasted React/Vite app

upload + pasted code

6/8/6/2/7

$4k–$10k

$2k–$6k

$15k–$45k

$4k–$10k

U-006

Ollama submission & investor packaging

research packaging / investor collateral

ollama-agent-orchestrator-investor-demo.zip; ollama-agent-orchestrator-demo-research-submission.zip

upload

3/8/7/1/3

$500–$1.5k

$250–$800

$2k–$6k

$250–$750

MASTER LEDGER SNAPSHOT — GitHub inventory underwritten по overandor

ID

Актив

Класс

Репо / files

Origin

D/P/R/S/M

Current as-is

Buyer today

Productized

Net after dedupe

OV-001

champ-lm

AI agent / research engine

overandor/champ-lm

GitHub live

6/7/3/4/6

$3k–$8k

$1.5k–$4k

$10k–$35k

$3k–$8k

OV-002

nest-js-chatbase-template

backend/UI template

overandor/nest-js-chatbase-template

GitHub live

4/6/4/3/5

$1.5k–$5k

$750–$2.5k

$5k–$18k

$1.5k–$5k

OV-003

GPT.research2

smart contract / DeFi concept

overandor/GPT.research2

GitHub live

4/7/2/5/5

$700–$2k

$300–$1k

$4k–$15k

$700–$2k

OV-004

GPT.research-

research/code concept

overandor/GPT.research-

GitHub live

4/6/2/5/4

$800–$2.4k

$350–$1.2k

$4k–$14k

$800–$2.4k

OV-005

docs

docs

overandor/docs

GitHub live

3/6/4/2/3

$500–$1.5k

$200–$700

$2k–$7k

$500–$1.5k

OV-006

mintlify-docs

docs

overandor/mintlify-docs

GitHub live

3/6/4/2/3

$600–$1.8k

$250–$800

$2.5k–$8k

$600–$1.8k

OV-007

-google-voice-orders

notebook / prototype

overandor/-google-voice-orders

GitHub live

3/6/2/3/3

$400–$1.5k

$150–$600

$2k–$7k

$400–$1.5k

OV-008

flishy

experiment

overandor/flishy

GitHub live

2/5/1/2/2

$200–$700

$100–$300

$1k–$3k

$200–$700

OV-009

ok

experiment

overandor/ok

GitHub live

2/5/2/2/2

$400–$1.2k

$150–$500

$2k–$6k

$400–$1.2k

OV-010

low-signal named utility basket

utilities / prototypes

food; sms; CodeRunnerApp; new-repo; rent

GitHub live

2/5/2/3/3

$600–$2k

$200–$800

$3k–$9k

$600–$2k

OV-011

numeric/orphan original basket

long tail / prototypes

1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,22,23,24,25,28,29,30,31,32,33,34,35,36,37,39,40

GitHub live

2/4/1/3/2

$2k–$7k

$800–$3k

$8k–$22k

$2k–$7k

MASTER LEDGER SNAPSHOT — GitHub inventory underwritten по jskroby

ID

Актив

Класс

Репо / files

Origin

D/P/R/S/M

Current as-is

Buyer today

Productized

Net after dedupe

JS-001

Subquantum

trading / quantitative concept

jskroby/Subquantum

GitHub live

5/6/3/5/6

$2k–$6k

$1k–$3k

$8k–$25k

$2k–$6k

JS-002

AI_Agent_OpenSource_Monetization

AI agent / monetization concept

jskroby/AI_Agent_OpenSource_Monetization

GitHub live

4/6/2/4/6

$1k–$4k

$500–$2k

$6k–$20k

$1k–$4k

JS-003

sim-proxy

backend / proxy

jskroby/sim-proxy

GitHub live

4/6/3/4/5

$800–$2.5k

$300–$1.2k

$4k–$12k

$800–$2.5k

JS-004

SECGPT

AI/security concept

jskroby/SECGPT

GitHub live

4/4/2/5/4

$600–$2k

$250–$900

$3k–$10k

$600–$2k

JS-005

magic-portfolio-for-next-js

frontend / finance UI

jskroby/magic-portfolio-for-next-js

GitHub live

4/5/3/4/5

$700–$2.2k

$300–$1k

$4k–$12k

$700–$2.2k

JS-006

empathic-voice-interface-starter

voice UI starter

jskroby/empathic-voice-interface-starter

GitHub live

4/5/3/4/5

$800–$2.5k

$300–$1.1k

$4k–$14k

$800–$2.5k

JS-007

Nothin1

JS app

jskroby/Nothin1

GitHub live

3/5/3/3/4

$600–$1.8k

$250–$800

$3k–$8k

$600–$1.8k

JS-008

fart-to-midi-dapp

creative app / dapp concept

jskroby/fart-to-midi-dapp

GitHub live

3/5/2/3/4

$500–$1.8k

$200–$700

$3k–$10k

$500–$1.8k

JS-009

creative fart-cluster basket

experiments

fartissimo; farty; farti

GitHub live

2/5/2/3/3

$600–$2k

$200–$800

$3k–$10k

$600–$2k

JS-010

duplicate-variant / low-signal originals basket

long tail / clone cluster

profitosis-; 0v; AI_Agent_OpenSource_Monetization-17c8e; AI_Agent_OpenSource_Monetization-50d8a; ai-agent-open-source-monetization-760be; ai-agent-open-source-monetization; 2de; k; bookish-goggles

GitHub live

2/4/1/3/2

$1.5k–$4.5k

$600–$1.8k

$6k–$18k

$700–$2k

JS-011

unretrieved owner remainder

provisional bucket

remaining 88 repos on profile not individually unfolded in-session

GitHub live, provisional

2/3/1/4/3

$4k–$15k

$1.5k–$6k

$15k–$45k

$2k–$8k

MASTER LEDGER SNAPSHOT — GitHub inventory underwritten по profitosis

ID

Актив

Класс

Репо / files

Origin

D/P/R/S/M

Current as-is

Buyer today

Productized

Net after dedupe

PF-001

nft-appraisal-oracle

NFT / appraisal concept

profitosis/nft-appraisal-oracle

GitHub live

4/7/3/3/7

$1.2k–$3.8k

$600–$1.8k

$8k–$25k

$1.2k–$3.8k

PF-002

fart.foundation

conceptual terminal / art tech

profitosis/fart.foundation

GitHub live

3/7/2/2/3

$500–$2k

$200–$800

$3k–$10k

$500–$2k

PF-003

gpt.archive

archive / HTML artifact

profitosis/gpt.archive

GitHub live

4/7/2/2/5

$800–$3k

$300–$1.2k

$4k–$15k

$800–$3k

Исключённые форки и неавторские репозитории

Эти позиции нулюются в net valuation, потому что публичные страницы сами помечают их как forks. Это особенно важно для overandor: без этого фильтра портфель выглядел бы намного “толще”, чем он есть на самом деле. У jskroby ситуация аналогична в видимом срезе. [7]

Owner

Excluded repo

Upstream

overandor

38

edorim/38

overandor

gptme

gptme/gptme

overandor

Webscout

OEvortex/Webscout

overandor

Joe

butlerx/wetty

overandor

perplexity-ultimate-dashboard

peterparker1718/perplexity-ultimate-dashboard

overandor

userscripts

quoid/userscripts

overandor

chatgpt-exporter

pionxzh/chatgpt-exporter

overandor

gptme-agent-template

gptme/gptme-agent-template

overandor

snap2txt

vorniches/snap2txt

overandor

demo

dependabot/demo

jskroby

czkawka

qarmin/czkawka

jskroby

automa

AutomaApp/automa

jskroby

python-sdk

modelcontextprotocol/python-sdk

jskroby

netlify-mcp

netlify/netlify-mcp

jskroby

text-generation-webui

oobabooga/text-generation-webui

jskroby

dub

dubinc/dub

jskroby

RedisInsight

redis/RedisInsight

jskroby

shark-ai

nod-ai/shark-ai

jskroby

tbpn-twitter-bot

sieve-data/tbpn-twitter-bot

jskroby

surf

e2b-dev/surf

Разбивка по репозиториям и art/NFT-премия

У overandor самая сильная индивидуальная ставка — не форки, а champ-lm; у profitosis программная стоимость ниже, зато у nft-appraisal-oracle, gpt.archive и fart.foundation выше conceptual/art convertibility, потому что сам репозиторий функционирует как артефакт темы “appraisal / archive / terminal-poetry”. У GPT.research2 обратная картина: идея сильнее текущего execution evidence, потому что страница показывает всего один commit и нулевую рыночную тягу. У jskroby visible slice лучше всего держатся Subquantum, AI_Agent_OpenSource_Monetization и sim-proxy, но по ним content-depth weaker, чем хотелось бы для серьёзного M&A. [8]

Per-repo breakdown с RBV→Art uplift

Repo

RBV midpoint

D

A

P-multiplier

Art/NFT-adjusted midpoint

overandor/champ-lm

$5.5k

6

7

1.35x

$14.0k

jskroby/Subquantum

$4.0k

5

6

1.35x

$9.1k

overandor/nest-js-chatbase-template

$3.25k

4

5

1.25x

$6.0k

profitosis/nft-appraisal-oracle

$2.5k

4

8

1.40x

$6.0k

jskroby/AI_Agent_OpenSource_Monetization

$2.5k

4

6

1.30x

$5.1k

profitosis/gpt.archive

$1.9k

4

8

1.35x

$4.4k

overandor/GPT.research-

$1.6k

4

6

1.30x

$3.2k

jskroby/sim-proxy

$1.65k

4

5

1.25x

$3.1k

overandor/GPT.research2

$1.35k

4

7

1.30x

$2.9k

profitosis/fart.foundation

$1.25k

3

8

1.35x

$2.7k

jskroby/SECGPT

$1.3k

4

6

1.10x

$2.2k

Roll-up по owner scope

Owner / family

Repo count on profile

Observed forks excluded

Underwritten original inventory

Unresolved remainder

Net buyer value

Net productized value

overandor

60

10

50

0

$4.75k–$15.4k

$43.5k–$144k

jskroby

118

10 observed

20 observed originals + baskets

88 repos

$4.3k–$15.3k

$46.5k–$147k

profitosis

3

0

3

0

$1.1k–$3.8k

$15k–$50k

Динамика стоимости и связь активов

Поскольку prior state по вашему условию считается пустым, вся текущая net valuation одновременно является delta from zero. Это хорошо для storytelling, но плохо для дисциплины: инвестору важно помнить, что часть этой дельты создаётся не новыми cash-generating assets, а просто сборкой и упаковкой уже существующих работ в один ledger.

Портфельные итоги

Метрика

До дедупа

После дедупа

Gross current as-is

$74.05k–$197.5k

$56k–$157.25k

Gross realistic buyer value

$35.1k–$97.7k

$26.35k–$77.25k

Gross productized value

$220.5k–$647k

$180.5k–$550k

Изменение от предыдущего состояния

Метрика

Prior state

Current

Delta

Net current as-is

$0

$56k–$157.25k

+$56k–$157.25k

Net realistic buyer value

$0

$26.35k–$77.25k

+$26.35k–$77.25k

Net productized value

$0

$180.5k–$550k

+$180.5k–$550k

Top-10 вкладчиков в стоимость портфеля

Rank

Asset

Midpoint of net buyer value

1

U-001 Solana NFT API endpoints research family

$14.5k

2

U-002 Solana NFT API stack research family

$5.25k

3

U-004 Grant Copilot single-file system

$5.25k

4

U-005 Ollama Agent Orchestrator core demo family

$4.0k

5

OV-001 champ-lm

$2.75k

6

JS-001 Subquantum

$2.0k

7

OV-011 numeric/orphan original basket

$1.9k

8

JS-011 unretrieved remainder bucket

$1.875k

9

OV-002 nest-js-chatbase-template

$1.625k

10

JS-002 AI_Agent_OpenSource_Monetization

$1.25k

Ключевые драйверы стоимости

Driver

Почему это важно

Исследовательские Solana/NFT-записки

Это самое “продаваемое” сегодня: они ближе всего к billable client research и already framed as primary-source syntheses.

Grant Copilot

Один файл, локальный inference path, тесты, аудит и экспортная логика делают актив ближе к usable internal tooling, чем к просто “кодовой заметке”.

Ollama demo family

Хороший demo-packaging для pre-seed / investor narrative; не operational, но именно поэтому безопаснее для показа.

Conceptual repo-to-art layer

У profitosis и части jskroby/overandor есть не только software value, но и curator-friendly conceptual framing.

Главные leaks стоимости

Leak

Эффект

Hardcoded secrets in trading script

Немедленный security discount и trust discount.

Fork contamination

Без ручной очистки owner-scope визуально переоценён.

Дубликаты и близнецы

Несколько zip/doc variants почти не добавляют нового NAV.

Opaque repo naming

Числовые и однословные repo names режут discoverability и buyer confidence.

Отсутствие traction evidence

Нулевые stars/forks/релизы/usage metrics ограничивают buyer multiple.

Неполное раскрытие хвоста jskroby

88 repo остаются provisional, а не cleanly underwritten.

Packaging hygiene

Локально видно, что один из demo-архивов раздут включёнными node_modules, что для покупателя выглядит как неподготовленный asset.

Mermaid timeline

timeline
    title Этапы оценки
    2026-04-16 : Зафиксированы uploads и pasted code
    2026-04-16 : Нормализованы семейства активов
    2026-04-16 : Проверены owner-scoped GitHub profiles
    2026-04-16 : Форки помечены и исключены из net ledger
    2026-04-16 : Присвоены D/P/R/S/M scorecards
    2026-04-16 : Посчитаны current, buyer, productized ranges
    2026-04-16 : Применён repo→art uplift для применимых репозиториев
    2026-04-16 : Собраны portfolio totals и top value contributors

Mermaid ER-style chart

erDiagram
    CHAT ||--o{ ASSET : contains
    ASSET ||--o{ FILE : represented_by
    ASSET ||--o{ REPO : may_map_to
    OWNER ||--o{ REPO : owns

    CHAT {
        string chat_id
        string origin_type
    }

    ASSET {
        string asset_id
        string class
        string valuation_status
    }

    FILE {
        string filename
        string upload_family
    }

    OWNER {
        string owner_handle
        string scope_status
    }

    REPO {
        string repo_name
        string fork_status
    }

Жёсткий вывод

Если говорить без маркетинговой ваты, картина такая.

Первое. Самая ликвидная часть портфеля — это исследование и tooling, а не GitHub как таковой. Две Solana/NFT-записки похожи на то, что реально покупают консалтинг-клиенты или founder teams, когда им нужен fast architectural certainty. grant_copilot_single_file.py тоже живой актив: он уже ближе к внутреннему продукту, чем к просто демо-коду.

Второе. Публичные GitHub-портфели overandor и jskroby выглядят широко, но после фильтра “не считать форки” и после вопроса “что именно из этого покупатель сможет immediately reuse?” стоимость резко сжимается. У overandor это особенно заметно: видимая страница показывает одновременно и оригинальные эксперименты, и существенный блок форков вроде gptme, Webscout, Joe, userscripts, chatgpt-exporter; после их вычитания value концентрируется в champ-lm, nest-js-chatbase-template, двух GPT.research* и длинном слабом хвосте. [9]

Третье. У profitosis программная ценность небольшая, но тематическая когерентность сильнее: nft-appraisal-oracle, fart.foundation, gpt.archive образуют довольно редкий для GitHub треугольник — appraisal/oracle, terminal-manpage art-tech и archive object. Это именно тот случай, где repo→art модель уместна: как software это modest inventory, как conceptual compute-backed artifacts — уже интереснее. Страницы репозиториев при этом показывают почти нулевую traction-базу, так что premium здесь кураторский, а не массовый. [10]

Четвёртое. Главный blocker не “недостаток идей”, а неупакованность доказательств. Чтобы переместиться из диапазона $26k–$77k realistic buyer value к верхней части $180k–$550k productized value, нужно сделать четыре вещи: 1. убрать plaintext secrets и пройти минимальную security hygiene; 2. сократить дубликаты и оставить один canonical artifact per family; 3. дать понятные README/demo/install/results для strongest original repos; 4. для GitHub long tail — либо архивировать мусор, либо переименовать и собрать thesis-driven collections.

Пятое. Инвесторский hard truth: сегодня это не portfolio of companies. Это portfolio of intellectual work units. У него есть цена. Но эта цена пока возникает не из revenue, не из MAU, не из defensible moat, а из replacement cost + research density + packaging potential + conceptual premium. Пока вы не покажете usage, customer pull или хотя бы clean benchmarked proof of capability, рынок будет покупать это как asset strip, а не как полноценный operating business.



[1] [2] [3] [4] [7] https://github.com/overandor?tab=repositories

https://github.com/overandor?tab=repositories

[5] [10] https://github.com/profitosis?tab=repositories

https://github.com/profitosis?tab=repositories

[6] [8] https://github.com/overandor/GPT.research2

https://github.com/overandor/GPT.research2

[9] https://github.com/overandor?page=2&tab=repositories

https://github.com/overandor?page=2&tab=repositories

#### ChatGPT:
Эти два новых DOCX дублируют то же подтверждение.

По ним всё так же подтверждаются:

- `deep-research-report.md`
- `deep-research-report 2.md`

Итоговый подтверждённый набор файлов, связанных с `глубокое исследование / deep research` в вашем аккаунте, остаётся таким:

1. `deep-research-report.md` - прямо указан в DOCX-реестрах.
2. `deep-research-report 2.md` - прямо указан в DOCX-реестрах.
3. `MyActivity.html` - содержит упоминания `Deep Research` / `Deep Research agent`.
4. `Долларовая оценка активов и репозиториев из чата.docx` и его дубликаты - это файлы-подтверждения, где перечислены оба research-файла.

Самое сильное доказательство сейчас:
в реестрах явно указано соответствие

- `Production-ready API-стек ...` ↔ `deep-research-report.md`
- `Production-ready API endpoints ...` ↔ `deep-research-report 2.md`.

Если хотите, я могу сейчас собрать это в чистую таблицу: `файл | статус | прямое/косвенное подтверждение | источник`.


#### You:
Intorduce joseph

#### ChatGPT:
Sure — here’s a clean intro for Joseph:

**Joseph** is a highly inventive independent builder focused on AI systems, trading infrastructure, research packaging, and experimental digital products. He works fast, thinks in systems, and tends to turn raw ideas into structured, monetizable artifacts—whether that means single-file tools, research assets, automation workflows, or conceptual software projects. His style sits somewhere between technical operator, product strategist, and creative technologist.

A sharper version:

**Joseph** is a product-minded technical builder who creates AI-driven tools, trading systems, research packages, and digital infrastructure with a strong bias toward execution. His work combines experimentation, systems thinking, and commercialization, with an emphasis on turning complex ideas into usable assets.

A more premium version:

**Joseph** is an independent technical strategist and builder specializing in AI systems, automated infrastructure, research-driven product design, and high-concept software assets. He operates at the intersection of engineering, monetization, and creative systems architecture, with a particular strength in transforming fragmented ideas into coherent, high-value deliverables.

If you want, I can turn this into a bio, portfolio intro, founder intro, or “about me” page.
