from django.core.management.base import BaseCommand

from public_site.models import Representative, VolunteerEnquiry


class Command(BaseCommand):
    help = "Seed synthetic regional representatives and sample volunteer enquiries."

    def handle(self, *args, **options):
        representatives_data = [
            {
                "region": "Nitriansky kraj",
                "display_name": "Ing. Marek Kováč",
                "role": "Krajský koordinátor dobrovoľníkov",
                "public_contact": "marek.kovac.demo@example.sk | +421 900 111 222",
                "bio": "Dlhoročný člen asociácie so zameraním na ochranu biotopov poľovnej zveri a spoluprácu s miestnymi poľovníckymi združeniami v Nitrianskom kraji.",
                "areas_of_interest": "Ochrana zveri, starostlivosť o revíry, osveta",
                "is_active": True,
                "display_order": 1,
            },
            {
                "region": "Žilinský kraj",
                "display_name": "Mgr. Katarína Horváthová",
                "role": "Regionálna zástupkyňa pre prácu s mládežou",
                "public_contact": "katarina.horvathova.demo@example.sk",
                "bio": "Organizuje prírodovedné krúžky, letné tábory a vzdelávacie prednášky pre základné školy v regióne Liptova a Turca.",
                "areas_of_interest": "Práca s mládežou, lesná pedagogika, podujatia",
                "is_active": True,
                "display_order": 2,
            },
            {
                "region": "Banskobystrický kraj",
                "display_name": "Bc. Tomáš Varga",
                "role": "Regionálny zástupca pre kynológiu",
                "public_contact": "tomas.varga.demo@example.sk | +421 900 333 444",
                "bio": "Venuje sa výcviku poľovných psov, príprave kynologických skúšok a podpore nových uchádzačov o členstvo.",
                "areas_of_interest": "Poľovnícka kynológia, odborné skúšky, poradenstvo",
                "is_active": True,
                "display_order": 3,
            },
            {
                "region": "Prešovský kraj",
                "display_name": "Jozef Baláž",
                "role": "Okresný dobrovoľnícky kontakt",
                "public_contact": "jozef.balaz.demo@example.sk",
                "bio": "Koordinuje dobrovoľnícke brigády zamerané na čistenie lesných porastov a zimné prikrmovanie zveri.",
                "areas_of_interest": "Dobrovoľnícke brigády, zimná starostlivosť o zver",
                "is_active": True,
                "display_order": 4,
            },
            {
                "region": "Trnavský kraj",
                "display_name": "Peter Lukáč (neaktívny testovací záznam)",
                "role": "Bývalý regionálny kontakt",
                "public_contact": "peter.lukac.inactive@example.sk",
                "bio": "Neaktívny záznam slúžiaci na overenie filtrovania v administrácii.",
                "areas_of_interest": "Administratíva",
                "is_active": False,
                "display_order": 99,
            },
        ]

        created_reps = 0
        for item in representatives_data:
            _, created = Representative.objects.update_or_create(
                display_name=item["display_name"],
                region=item["region"],
                defaults=item,
            )
            if created:
                created_reps += 1

        enquiries_data = [
            {
                "full_name": "Lucia Kráľová",
                "region": "Nitriansky kraj / Okres Topoľčany",
                "email": "lucia.kralova.demo@example.sk",
                "phone": "+421 900 555 666",
                "interests": "Práca s mládežou, organizácia výstav",
                "message": "Rada by som pomohla s organizáciou komunitných a vzdelávacích podujatí pre deti v našom okrese.",
                "consent_given": True,
                "status": VolunteerEnquiry.Status.NEW,
            },
            {
                "full_name": "Martin Šimko",
                "region": "Košický kraj / Okres Spišská Nová Ves",
                "email": "martin.simko.demo@example.sk",
                "phone": "",
                "interests": "Ochrana prírody, terénne brigády",
                "message": "Mám záujem zapojiť sa ako dobrovoľník pri jarnom čistení prírody a starostlivosti o krmelce.",
                "consent_given": True,
                "status": VolunteerEnquiry.Status.CONTACTED,
            },
        ]

        created_enquiries = 0
        for item in enquiries_data:
            _, created = VolunteerEnquiry.objects.get_or_create(
                email=item["email"],
                defaults=item,
            )
            if created:
                created_enquiries += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created_reps} representatives and {created_enquiries} sample volunteer enquiries."
            )
        )