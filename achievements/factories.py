import uuid
import factory
from factory import fuzzy
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.files.base import ContentFile

from django.contrib.auth import get_user_model
from students.models import Student
from achievements.models import (
	Achievement,
	Skill,
	Education,
	Experience,
	Publication,
	Project,
	ResumeProfile,
)

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = User

	username = factory.Sequence(lambda n: f"user{n}")
	email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
	is_active = True
	is_staff = False
	is_superuser = False


class StudentFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = Student

	roll_number = factory.Sequence(lambda n: f"RN{n:05d}")
	first_name = factory.Faker("first_name")
	last_name = factory.Faker("last_name")
	date_of_birth = factory.Faker("date_of_birth")
	gender = fuzzy.FuzzyChoice(["M", "F", "O"])
	# Optional fields left as None/defaults to keep instances minimal
	email = factory.LazyAttribute(lambda o: f"{o.roll_number.lower()}@student.test")
	enrollment_date = factory.LazyFunction(timezone.now)
	status = "ACTIVE"

	# Link to auth user (optional); some code may expect one
	@factory.post_generation
	def user(self, create, extracted, **kwargs):
		if not create:
			return
		if extracted is True:
			# create a user with same identity
			self.user = UserFactory(username=self.roll_number.lower())
			self.save()
		elif isinstance(extracted, User):
			self.user = extracted
			self.save()


class OwnedEntityFactoryMixin:
	"""
	Mixin to populate generic owner fields against a Student before create.
	Allows optional kwarg 'student' to specify the owner student.
	"""
	@classmethod
	def _create(cls, model_class, *args, **kwargs):
		student_obj = kwargs.pop("student", None) or StudentFactory()
		kwargs.setdefault("owner_content_type", ContentType.objects.get_for_model(Student))
		kwargs.setdefault("owner_object_id", student_obj.id)
		kwargs.setdefault("owner_type", "students.student")
		obj = super()._create(model_class, *args, **kwargs)
		# attach convenience attribute for tests
		setattr(obj, "student", student_obj)
		return obj

	@factory.lazy_attribute
	def created_by(self):
		return None

	@factory.lazy_attribute
	def updated_by(self):
		return None


class AchievementFactory(OwnedEntityFactoryMixin, factory.django.DjangoModelFactory):
	class Meta:
		model = Achievement

	id = factory.LazyFunction(uuid.uuid4)
	title = factory.Faker("sentence", nb_words=4)
	category = fuzzy.FuzzyChoice([v for v, _ in Achievement._meta.get_field("category").choices])
	description = factory.Faker("paragraph")
	issuer_or_organizer = factory.Faker("company")
	location = factory.Faker("city")
	start_date = factory.Faker("date_object")
	end_date = None
	achieved_on = factory.Faker("date_object")
	url = factory.Faker("url")
	metadata = factory.LazyFunction(dict)
	is_public = True

	@factory.post_generation
	def certificate_file(self, create, extracted, **kwargs):
		if not create:
			return
		if extracted is True:
			# Create a small dummy file
			self.certificate_file.save(
				f"certificate_{self.id}.txt",
				ContentFile(b"dummy certificate content"),
				save=True,
			)
		elif extracted:
			self.certificate_file = extracted
			self.save()


class SkillFactory(OwnedEntityFactoryMixin, factory.django.DjangoModelFactory):
	class Meta:
		model = Skill

	id = factory.LazyFunction(uuid.uuid4)
	name = factory.Faker("job")
	proficiency = fuzzy.FuzzyInteger(0, 100)
	years_of_experience = None
	is_core = fuzzy.FuzzyChoice([True, False])


class EducationFactory(OwnedEntityFactoryMixin, factory.django.DjangoModelFactory):
	class Meta:
		model = Education

	id = factory.LazyFunction(uuid.uuid4)
	institution = factory.Faker("company")
	degree = factory.Faker("job")
	field_of_study = factory.Faker("word")
	start_date = factory.Faker("date_object")
	end_date = None
	description = factory.Faker("sentence")


class ExperienceFactory(OwnedEntityFactoryMixin, factory.django.DjangoModelFactory):
	class Meta:
		model = Experience

	id = factory.LazyFunction(uuid.uuid4)
	title = factory.Faker("job")
	organization = factory.Faker("company")
	start_date = factory.Faker("date_object")
	end_date = None
	currently_working = False
	location = factory.Faker("city")
	responsibilities = factory.Faker("paragraph")
	metadata = factory.LazyFunction(dict)


class PublicationFactory(OwnedEntityFactoryMixin, factory.django.DjangoModelFactory):
	class Meta:
		model = Publication

	id = factory.LazyFunction(uuid.uuid4)
	title = factory.Faker("sentence", nb_words=5)
	authors = factory.Faker("name")
	journal_or_conference = factory.Faker("sentence", nb_words=3)
	year = fuzzy.FuzzyInteger(1990, timezone.now().year)
	doi = factory.LazyAttribute(lambda o: f"10.1000/{uuid.uuid4().hex[:8]}")
	url = factory.Faker("url")


class ProjectFactory(OwnedEntityFactoryMixin, factory.django.DjangoModelFactory):
	class Meta:
		model = Project

	id = factory.LazyFunction(uuid.uuid4)
	title = factory.Faker("sentence", nb_words=4)
	description = factory.Faker("paragraph")
	start_date = factory.Faker("date_object")
	end_date = None
	role = factory.Faker("job")
	technologies = factory.LazyFunction(list)
	url = factory.Faker("url")
	repository_url = factory.Faker("url")


class ResumeProfileFactory(OwnedEntityFactoryMixin, factory.django.DjangoModelFactory):
	class Meta:
		model = ResumeProfile

	id = factory.LazyFunction(uuid.uuid4)
	headline = factory.Faker("sentence", nb_words=6)
	summary = factory.Faker("paragraph")
	location = factory.Faker("city")
	website = factory.Faker("url")
	links = factory.LazyFunction(list)


