import factory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker
from datetime import datetime, timedelta
import random
import json

from app.models.user import User
from app.models.health_record import HealthRecord
from app.models.vital_signs import VitalSign
from app.core.security import get_password_hash
from app.core.database import SessionLocal

fake = Faker()

class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = SessionLocal()
        sqlalchemy_session_persistence = "commit"

class UserFactory(BaseFactory):
    class Meta:
        model = User
    
    email = factory.LazyAttribute(lambda x: fake.unique.email())
    full_name = factory.LazyAttribute(lambda x: fake.name())
    hashed_password = factory.LazyAttribute(lambda x: get_password_hash("TestPass123!"))
    is_active = True
    is_superuser = False
    created_at = factory.LazyAttribute(lambda x: fake.date_time_between(start_date='-1y', end_date='now'))
    
    @factory.post_generation
    def health_records(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            for record in extracted:
                self.health_records.append(record)
        else:
            # Create random number of health records
            num_records = random.randint(0, 10)
            for _ in range(num_records):
                HealthRecordFactory(user=self)

class AdminUserFactory(UserFactory):
    is_superuser = True
    email = factory.Sequence(lambda n: f"admin{n}@example.com")

class HealthRecordFactory(BaseFactory):
    class Meta:
        model = HealthRecord
    
    user = factory.SubFactory(UserFactory)
    record_type = factory.LazyAttribute(lambda x: random.choice([
        "lab_result", "prescription", "imaging", "consultation", 
        "vaccination", "surgery", "allergy", "condition"
    ]))
    record_date = factory.LazyAttribute(lambda x: fake.date_time_between(start_date='-2y', end_date='now'))
    title = factory.LazyAttribute(lambda x: fake.sentence(nb_words=4))
    description = factory.LazyAttribute(lambda x: fake.text(max_nb_chars=200))
    category = factory.LazyAttribute(lambda x: random.choice([
        "laboratory", "pharmacy", "radiology", "general",
        "cardiology", "neurology", "orthopedics", "pediatrics"
    ]))
    body_part = factory.LazyAttribute(lambda x: random.choice([
        None, "head", "chest", "abdomen", "heart", 
        "lungs", "liver", "kidney", "spine"
    ]))
    severity = factory.LazyAttribute(lambda x: random.choice([None, "low", "medium", "high", "critical"]))
    metadata = factory.LazyAttribute(lambda x: {
        "generated": True,
        "test_id": fake.uuid4(),
        "additional_notes": fake.sentence()
    })
    tags = factory.LazyAttribute(lambda x: random.sample(
        ["urgent", "follow-up", "routine", "annual", "emergency", "preventive"],
        k=random.randint(0, 3)
    ))
    created_at = factory.LazyAttribute(lambda x: x.record_date)
    updated_at = factory.LazyAttribute(lambda x: x.created_at + timedelta(days=random.randint(0, 30)))

class VitalSignFactory(BaseFactory):
    class Meta:
        model = VitalSign
    
    user = factory.SubFactory(UserFactory)
    recorded_at = factory.LazyAttribute(lambda x: fake.date_time_between(start_date='-6m', end_date='now'))
    blood_pressure_systolic = factory.LazyAttribute(lambda x: random.randint(90, 140))
    blood_pressure_diastolic = factory.LazyAttribute(lambda x: random.randint(60, 90))
    heart_rate = factory.LazyAttribute(lambda x: random.randint(50, 120))
    temperature = factory.LazyAttribute(lambda x: round(random.uniform(35.5, 38.5), 1))
    weight = factory.LazyAttribute(lambda x: round(random.uniform(45, 120), 1))
    height = factory.LazyAttribute(lambda x: random.randint(140, 200))
    bmi = factory.LazyAttribute(lambda x: round(x.weight / ((x.height / 100) ** 2), 1))
    oxygen_saturation = factory.LazyAttribute(lambda x: random.randint(92, 100))
    glucose_level = factory.LazyAttribute(lambda x: random.randint(70, 180))
    notes = factory.LazyAttribute(lambda x: fake.sentence() if random.random() > 0.5 else None)

class TestDataGenerator:
    """Generate comprehensive test data sets"""
    
    @staticmethod
    def create_user_with_full_history(email=None):
        """Create a user with complete medical history"""
        user = UserFactory(email=email or fake.unique.email())
        
        # Create varied health records
        record_types = ["lab_result", "prescription", "imaging", "consultation"]
        for record_type in record_types:
            for _ in range(random.randint(2, 5)):
                HealthRecordFactory(user=user, record_type=record_type)
        
        # Create vital signs history
        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            VitalSignFactory(user=user, recorded_at=date)
        
        return user
    
    @staticmethod
    def create_diabetic_patient():
        """Create a patient with diabetes-related records"""
        user = UserFactory(full_name="Diabetic Patient Test")
        
        # Glucose monitoring records
        for i in range(90):  # 3 months of data
            date = datetime.now() - timedelta(days=i)
            glucose = 100 + random.randint(-30, 80)  # Variable glucose levels
            VitalSignFactory(
                user=user,
                recorded_at=date,
                glucose_level=glucose,
                notes="Fasting" if i % 2 == 0 else "Post-meal"
            )
        
        # Related health records
        HealthRecordFactory(
            user=user,
            record_type="condition",
            title="Type 2 Diabetes Diagnosis",
            category="endocrinology",
            severity="high",
            metadata={"condition": "diabetes_type_2", "hba1c": 7.5}
        )
        
        HealthRecordFactory(
            user=user,
            record_type="prescription",
            title="Metformin Prescription",
            category="pharmacy",
            metadata={"medication": "metformin", "dosage": "500mg", "frequency": "twice daily"}
        )
        
        return user
    
    @staticmethod
    def create_cardiac_patient():
        """Create a patient with cardiac-related records"""
        user = UserFactory(full_name="Cardiac Patient Test")
        
        # Blood pressure monitoring
        for i in range(60):  # 2 months of data
            date = datetime.now() - timedelta(days=i)
            systolic = 130 + random.randint(-10, 20)
            diastolic = 85 + random.randint(-5, 10)
            VitalSignFactory(
                user=user,
                recorded_at=date,
                blood_pressure_systolic=systolic,
                blood_pressure_diastolic=diastolic,
                heart_rate=70 + random.randint(-10, 20)
            )
        
        # Cardiac-related records
        HealthRecordFactory(
            user=user,
            record_type="imaging",
            title="Echocardiogram Results",
            body_part="heart",
            category="cardiology",
            severity="medium",
            metadata={"ejection_fraction": 55, "wall_motion": "normal"}
        )
        
        HealthRecordFactory(
            user=user,
            record_type="lab_result",
            title="Lipid Panel",
            category="laboratory",
            metadata={
                "total_cholesterol": 220,
                "ldl": 140,
                "hdl": 45,
                "triglycerides": 175
            }
        )
        
        return user
    
    @staticmethod
    def create_pediatric_patient():
        """Create a pediatric patient with vaccination records"""
        user = UserFactory(full_name="Pediatric Patient Test")
        
        # Vaccination records
        vaccines = [
            ("Hepatitis B", "birth"),
            ("DTaP", "2 months"),
            ("Hib", "2 months"),
            ("IPV", "2 months"),
            ("PCV13", "2 months"),
            ("RV", "2 months"),
            ("DTaP", "4 months"),
            ("Hib", "4 months"),
            ("IPV", "4 months"),
            ("PCV13", "4 months"),
            ("RV", "4 months"),
            ("DTaP", "6 months"),
            ("PCV13", "6 months"),
            ("Influenza", "6 months"),
            ("MMR", "12 months"),
            ("Varicella", "12 months"),
            ("Hepatitis A", "12 months")
        ]
        
        for vaccine, age in vaccines:
            HealthRecordFactory(
                user=user,
                record_type="vaccination",
                title=f"{vaccine} Vaccination",
                category="pediatrics",
                metadata={"vaccine": vaccine, "age_given": age, "lot_number": fake.uuid4()[:8]}
            )
        
        # Growth chart data
        for month in range(24):
            date = datetime.now() - timedelta(days=month * 30)
            weight = 3.5 + (month * 0.5)  # Simplified growth curve
            height = 50 + (month * 2.5)  # Simplified growth curve
            VitalSignFactory(
                user=user,
                recorded_at=date,
                weight=weight,
                height=height,
                notes=f"Well-child visit at {month} months"
            )
        
        return user
    
    @staticmethod
    def create_test_database(num_users=10):
        """Create a complete test database with various patient profiles"""
        users = []
        
        # Create admin user
        admin = AdminUserFactory(email="admin@healthstash.test")
        users.append(admin)
        
        # Create regular users with varied profiles
        users.append(TestDataGenerator.create_diabetic_patient())
        users.append(TestDataGenerator.create_cardiac_patient())
        users.append(TestDataGenerator.create_pediatric_patient())
        
        # Create random users with full histories
        for _ in range(num_users - 4):
            users.append(TestDataGenerator.create_user_with_full_history())
        
        return users
    
    @staticmethod
    def create_stress_test_data(num_records=1000):
        """Create large dataset for stress testing"""
        user = UserFactory(email="stress_test@example.com")
        
        records = []
        for i in range(num_records):
            record = HealthRecordFactory(
                user=user,
                title=f"Stress Test Record {i}",
                metadata={"index": i, "batch": "stress_test"}
            )
            records.append(record)
            
            if i % 100 == 0:
                print(f"Created {i} records...")
        
        return user, records