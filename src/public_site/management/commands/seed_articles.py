from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from public_site.models import Article, Category, FAQ


class Command(BaseCommand):
    help = "Seed demo categories, articles, and FAQs for the public website."

    def handle(self, *args, **options):
        categories_data = [
            {
                "name": "Ochrana prírody",
                "slug": "ochrana-prirody",
                "description": "Projekty obnovy biotopov, starostlivosť o zver a ekologické iniciatívy v revíroch.",
            },
            {
                "name": "Legislatíva a správy",
                "slug": "legislativa-a-spravy",
                "description": "Aktuálne informácie z komory, zmeny v predpisoch a metodické usmernenia pre poľovníkov.",
            },
            {
                "name": "Podujatia a kynológia",
                "slug": "podujatia-a-kynologia",
                "description": "Vzdelávacie semináre, chovateľské prehliadky, strelecké súťaže a poľovnícka kynológia.",
            },
        ]

        categories = {}
        for item in categories_data:
            cat, _ = Category.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "description": item["description"],
                },
            )
            categories[item["slug"]] = cat

        now = timezone.now()

        articles_data = [
            {
                "title": "Zimné prikrmovanie zveri: zásady správnej starostlivosti v revíroch",
                "slug": "zimne-prikrmovanie-zveri-zasady-spravnej-starostlivosti",
                "category": categories["ochrana-prirody"],
                "author_byline": "Ing. Marek Kováč",
                "summary": "Správne načasovanie a výber vhodného krmiva pomáhajú raticovej aj malej zveri prekonať náročné zimné obdobie bez škôd na lesných porastoch.",
                "body": (
                    "Starostlivosť o zver v období núdze patrí medzi základné zákonné aj etické povinnosti každého užívateľa poľovného revíru.\n\n"
                    "Kľúčom k úspešnému prikrmovaniu je pravidelnosť, hygiena kŕmnych zariadení a predovšetkým biologicky vhodná skladba krmiva. Objemové krmivo, ako je kvalitné lúčne seno a letnina, musí byť zveri prístupné v suchom stave počas celej zimy.\n\n"
                    "Regionálne organizácie SPK zároveň pripomínajú potrebu kontroly solísk a vodných zdrojov, ktoré zohrávajú dôležitú úlohu pri udržiavaní dobrej kondície populácií."
                ),
                "cover_image": "https://images.unsplash.com/photo-1484406566174-9da000fda645?auto=format&fit=crop&w=1000&q=80",
                "status": Article.Status.PUBLISHED,
                "published_at": now - timedelta(days=12),
            },
            {
                "title": "Obnova remízok a biopásov pre malú zver na južnom Slovensku",
                "slug": "obnova-remizok-a-biopasov-pre-malu-zver",
                "category": categories["ochrana-prirody"],
                "author_byline": "RNDr. Jana Horváthová",
                "summary": "Dobrovoľníci a poľovnícke združenia vysadili viac ako 4 500 pôvodných drevín a kríkov, ktoré poskytnú úkryt a potravu pre zajace, bažanty a spevavce.",
                "body": (
                    "Intenzívne poľnohospodárstvo v nížinných oblastiach dlhodobo znižuje prirodzenú úživnosť krajiny. Slovenská poľovnícka komora preto podporuje zakladanie viacdruhových biopásov a výsadbu vetrolamov.\n\n"
                    "Počas jesennej etapy sa do výsadby zapojilo vyše dvadsať poľovníckych združení v spolupráci s miestnymi samosprávami a školami.\n\n"
                    "Nové krajinné prvky nielen chránia pôdu pred veternou eróziou a zadržiavajú vlahu, ale vytvárajú aj bezpečné hniezdiská pre poľnú zver."
                ),
                "cover_image": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1000&q=80",
                "status": Article.Status.PUBLISHED,
                "published_at": now - timedelta(days=9),
            },
            {
                "title": "Prehľad legislatívnych zmien a povinností pred novou poľovníckou sezónou",
                "slug": "prehlad-legislativnych-zmien-pred-novou-sezonou",
                "category": categories["legislativa-a-spravy"],
                "author_byline": "JUDr. Peter Varga",
                "summary": "Zhrnutie aktuálnych metodických pokynov týkajúcich sa evidencie lovu, veterinárnych opatrení a predlžovania platnosti poľovných lístkov.",
                "body": (
                    "Pred začiatkom novej poľovníckej sezóny odporúčame všetkým členom skontrolovať platnosť poľovných lístkov a dokladov o povinnom poistení.\n\n"
                    "Kancelária komory pripravila prehľadnú príručku k aktuálnym veterinárnym nariadeniam, vrátane odberu vzoriek a hlásenia úhynov zveri.\n\n"
                    "Záujemcovia o predĺženie poľovného lístka môžu využiť konzultačné hodiny na príslušných obvodných poľovníckych komorách."
                ),
                "cover_image": "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=1000&q=80",
                "status": Article.Status.PUBLISHED,
                "published_at": now - timedelta(days=7),
            },
            {
                "title": "Ako prebieha príprava uchádzačov o prvý poľovný lístok v praxi",
                "slug": "ako-prebieha-priprava-uchadzacov-o-prvy-polovny-listok",
                "category": categories["legislativa-a-spravy"],
                "author_byline": "Ing. Tomáš Belan",
                "summary": "Od teoretickej výučby zoológie a poľovníckej etiky až po praktickú stáž v revíri a streleckú prípravu pod vedením skúsených lektorov.",
                "body": (
                    "Vstup do poľovníckej komunity si vyžaduje dôkladnú teoretickú aj praktickú prípravu. Kurz pre uchádzačov o poľovný lístok zahŕňa biológiu zveri, starostlivosť o prostredie, kynológiu, strelectvo a prvú pomoc.\n\n"
                    "Neoddeliteľnou súčasťou je ročná praktická stáž v poľovnom revíri, kde kandidáti spoznávajú každodennú prácu poľovníkov pri budovaní kŕmnych zariadení a ochrane prírody.\n\n"
                    "Nové kurzy sa otvárajú pravidelne v jednotlivých regiónoch Slovenska."
                ),
                "cover_image": "https://images.unsplash.com/photo-1511497584788-876760111969?auto=format&fit=crop&w=1000&q=80",
                "status": Article.Status.PUBLISHED,
                "published_at": now - timedelta(days=5),
            },
            {
                "title": "Celoslovenské skúšky poľovných psov potvrdili vysokú úroveň kynológie",
                "slug": "celoslovenske-skusky-polovnych-psov-potvrdili-uroven",
                "category": categories["podujatia-a-kynologia"],
                "author_byline": "Mgr. Lukáš Kráľ",
                "summary": "Viac ako štyridsať vodičov so svojimi psami predviedlo vynikajúcu prácu na stope, dohľadávanie a poslušnosť v náročnom lesnom teréne.",
                "body": (
                    "Poľovnícka kynológia je vizitkou etického poľovníctva. Bez spoľahlivo vycvičeného poľovníckeho psa nie je možné zabezpečiť zodpovedné dohľadávanie zveri.\n\n"
                    "Tohtoročné skúšky priniesli mimoriadne vyrovnané výkony v kategórii stavačov aj farbiarov. Rozhodcovský zbor ocenil najmä disciplínu vodičov a systematickú prácu regionálnych kynologických klubov.\n\n"
                    "Ďakujeme všetkým organizátorom a dobrovoľníkom za bezchybný priebeh podujatia."
                ),
                "cover_image": "https://images.unsplash.com/photo-1548199973-03cce0bbc87b?auto=format&fit=crop&w=1000&q=80",
                "status": Article.Status.PUBLISHED,
                "published_at": now - timedelta(days=3),
            },
            {
                "title": "Jarné chovateľské prehliadky trofejí a vzdelávacie dni pre verejnosť",
                "slug": "jarne-chovatelske-prehliadky-trofeji-a-vzdelavacie-dni",
                "category": categories["podujatia-a-kynologia"],
                "author_byline": "Ing. Zuzana Bieliková",
                "summary": "Okresné organizácie pripravujú odborné hodnotenie uplynulej sezóny spojené s lesnou pedagogikou pre základné školy a rodiny s deťmi.",
                "body": (
                    "Chovateľské prehliadky nie sú len odborným zhodnotením kvality chovu a správnosti selektívneho lovu, ale aj príležitosťou priblížiť prácu poľovníkov širokej verejnosti.\n\n"
                    "Súčasťou sprievodného programu budú prednášky lesných pedagógov, ukážky vábenia zveri, sokoliarstva a ochrany horských ekosystémov.\n\n"
                    "Vstup na verejné časti výstav je voľný pre všetkých záujemcov o prírodu."
                ),
                "cover_image": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1000&q=80",
                "status": Article.Status.PUBLISHED,
                "published_at": now - timedelta(days=1),
            },
            {
                "title": "Pripravovaná metodika monitoringu veľkých šeliem (Koncept)",
                "slug": "pripravovana-metodika-monitoringu-velkych-seliem",
                "category": categories["ochrana-prirody"],
                "author_byline": "Redakcia SPK",
                "summary": "Rozpracovaný interný materiál k zberu pobytových znakov a fotopascí v horských revíroch.",
                "body": "Tento článok je v stave rozpracovaného konceptu (DRAFT) a slúži na overenie náhľadu pre redaktorov v administrácii.",
                "cover_image": "",
                "status": Article.Status.DRAFT,
                "published_at": None,
            },
        ]

        for item in articles_data:
            Article.objects.update_or_create(
                slug=item["slug"],
                defaults=item,
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully seeded 3 categories, 6 published articles, and 1 draft article."
            )
        )