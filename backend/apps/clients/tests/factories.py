import factory

from apps.clients.models import Client


class ClientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Client

    company_name = factory.Sequence(lambda n: f"Sample Client {n + 1}")
    contact_person = factory.Sequence(lambda n: f"Contact Person {n + 1}")
    email = factory.Sequence(lambda n: f"contact{n + 1}@client{n + 1}.test")
    phone = "+63 917 555 0100"
    address = "Unit 1, Sample Building, Makati City"
