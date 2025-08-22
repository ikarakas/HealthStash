#!/usr/bin/env python3

import os
import random
import uuid
import json
import datetime
from faker import Faker
from PIL import Image, ImageDraw
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import psycopg2
from minio import Minio

fake = Faker()

# Configuration
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'healthstash')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'healthstash')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'changeme')

MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')

# Sample data categories
RECORD_TYPES = [
    'Lab Results', 'X-Ray', 'MRI Scan', 'CT Scan', 'Prescription',
    'Vaccination Record', 'Surgery Report', 'Consultation Notes',
    'Blood Test', 'ECG Report', 'Ultrasound', 'Pathology Report',
    'Discharge Summary', 'Referral Letter', 'Medical Certificate',
    'Allergy Test', 'Vision Test', 'Hearing Test', 'Dental Records',
    'Physical Therapy', 'Mental Health Assessment', 'Cardiology Report'
]

BODY_PARTS = [
    'head', 'chest', 'abdomen', 'left_arm', 'right_arm', 
    'left_leg', 'right_leg', 'spine', 'heart', 'lungs',
    'liver', 'kidneys', 'brain', 'eyes', 'ears', 'teeth'
]

CATEGORIES = [
    'imaging', 'laboratory', 'clinical', 'surgical', 'emergency',
    'preventive', 'diagnostic', 'therapeutic', 'rehabilitation'
]

MEDICAL_TERMS = {
    'Lab Results': ['Hemoglobin', 'White Blood Cell Count', 'Cholesterol', 'Glucose', 'Creatinine'],
    'X-Ray': ['Chest X-Ray', 'Spine X-Ray', 'Hand X-Ray', 'Knee X-Ray', 'Dental X-Ray'],
    'MRI Scan': ['Brain MRI', 'Spine MRI', 'Knee MRI', 'Shoulder MRI', 'Abdominal MRI'],
    'Blood Test': ['Complete Blood Count', 'Lipid Panel', 'Liver Function', 'Thyroid Panel', 'Iron Studies'],
    'Prescription': ['Amoxicillin 500mg', 'Lisinopril 10mg', 'Metformin 850mg', 'Omeprazole 20mg', 'Atorvastatin 40mg']
}

def generate_medical_image(width=800, height=600, record_type="X-Ray"):
    """Generate a realistic-looking medical image"""
    img = Image.new('RGB', (width, height), color=(20, 20, 25))
    draw = ImageDraw.Draw(img)
    
    # Add some medical-looking patterns
    if "X-Ray" in record_type:
        # X-ray style (grayscale with bones)
        for i in range(0, width, 50):
            gray = random.randint(40, 80)
            draw.rectangle([i, 0, i+50, height], fill=(gray, gray, gray))
        # Add some "bone" structures
        draw.ellipse([width//3, height//3, 2*width//3, 2*height//3], 
                    fill=(200, 200, 200), outline=(180, 180, 180), width=3)
    elif "MRI" in record_type or "CT" in record_type:
        # MRI/CT scan style (circular with gradients)
        center_x, center_y = width//2, height//2
        for radius in range(min(width, height)//2, 0, -20):
            gray = 255 - (radius * 255 // (min(width, height)//2))
            draw.ellipse([center_x-radius, center_y-radius, 
                         center_x+radius, center_y+radius],
                        fill=(gray, gray, gray))
    elif "ECG" in record_type:
        # ECG style (waveform)
        points = []
        for x in range(0, width, 5):
            y = height//2 + random.randint(-100, 100)
            points.append((x, y))
        if len(points) > 1:
            draw.line(points, fill=(0, 255, 0), width=2)
    else:
        # Generic medical scan
        for _ in range(20):
            x, y = random.randint(0, width), random.randint(0, height)
            radius = random.randint(10, 50)
            gray = random.randint(100, 200)
            draw.ellipse([x-radius, y-radius, x+radius, y+radius],
                        fill=(gray, gray, gray), outline=(gray-20, gray-20, gray-20))
    
    # Add metadata overlay
    draw.text((10, 10), f"{record_type}", fill=(255, 255, 255))
    draw.text((10, 30), f"Patient ID: {fake.uuid4()[:8]}", fill=(255, 255, 255))
    draw.text((10, 50), f"Date: {fake.date()}", fill=(255, 255, 255))
    draw.text((10, height-30), f"Dr. {fake.last_name()}, MD", fill=(255, 255, 255))
    
    return img

def generate_medical_pdf(record_type, file_size_mb=1):
    """Generate a medical PDF report"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"{record_type} Report")
    
    # Patient info
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Patient: {fake.name()}")
    c.drawString(50, height - 100, f"DOB: {fake.date_of_birth()}")
    c.drawString(50, height - 120, f"MRN: {fake.uuid4()[:8].upper()}")
    c.drawString(50, height - 140, f"Date: {fake.date()}")
    
    # Medical content
    y_position = height - 180
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position, "Clinical Findings:")
    y_position -= 30
    
    c.setFont("Helvetica", 11)
    
    # Add medical terms specific to record type
    terms = MEDICAL_TERMS.get(record_type.split()[0] if ' ' in record_type else record_type, 
                              ['Normal findings', 'No abnormalities detected'])
    
    for term in terms:
        value = f"{random.uniform(0.5, 150):.2f}"
        unit = random.choice(['mg/dL', 'mmol/L', 'g/dL', 'IU/L', '%', 'mm'])
        status = random.choice(['Normal', 'Within range', 'Slightly elevated', 'Borderline'])
        
        c.drawString(70, y_position, f"• {term}: {value} {unit} - {status}")
        y_position -= 25
    
    # Add some lorem ipsum medical text to increase file size
    c.setFont("Helvetica-Bold", 14)
    y_position -= 20
    c.drawString(50, y_position, "Clinical Notes:")
    y_position -= 30
    
    c.setFont("Helvetica", 10)
    medical_text = [
        "Physical examination reveals no acute distress. Vital signs stable.",
        "Patient presents with symptoms consistent with diagnosis.",
        "Recommend follow-up in 3-6 months for re-evaluation.",
        "Continue current medication regimen as prescribed.",
        "Laboratory values within normal limits except as noted above.",
        "No contraindications for proposed treatment plan identified.",
        "Patient education provided regarding condition management."
    ]
    
    # Add pages to reach desired file size
    pages_needed = max(1, int(file_size_mb * 3))  # Approximate pages for size
    
    for page in range(pages_needed):
        if page > 0:
            c.showPage()
            y_position = height - 50
            c.setFont("Helvetica", 10)
        
        for _ in range(30):  # Lines per page
            if y_position < 100:
                break
            text = random.choice(medical_text) + " " + fake.text(max_nb_chars=100)
            # Word wrap
            words = text.split()
            line = ""
            for word in words:
                if len(line + word) < 80:
                    line += word + " "
                else:
                    c.drawString(70, y_position, line)
                    y_position -= 15
                    line = word + " "
            if line:
                c.drawString(70, y_position, line)
                y_position -= 15
    
    # Footer
    c.setFont("Helvetica", 10)
    c.drawString(50, 50, f"Physician: Dr. {fake.name()}, MD")
    c.drawString(50, 35, f"License #: {fake.uuid4()[:8].upper()}")
    
    c.save()
    return buffer.getvalue()

def create_sample_file(record_type, target_size_mb):
    """Create a sample medical file of specified size"""
    file_type = random.choice(['pdf', 'image'])
    
    if file_type == 'pdf' or 'Report' in record_type or 'Summary' in record_type:
        # Generate PDF
        content = generate_medical_pdf(record_type, target_size_mb)
        file_extension = 'pdf'
    else:
        # Generate image
        # Calculate dimensions for target size
        # Rough estimate: 1MB ≈ 1000x1000 pixels for JPEG
        dimension = int(1000 * (target_size_mb ** 0.5))
        img = generate_medical_image(dimension, dimension, record_type)
        
        buffer = io.BytesIO()
        # Adjust quality to reach target size
        quality = 95
        img.save(buffer, format='JPEG', quality=quality)
        
        # Fine-tune size
        while buffer.tell() < target_size_mb * 1024 * 1024 * 0.8 and quality > 10:
            buffer = io.BytesIO()
            quality -= 5
            img.save(buffer, format='JPEG', quality=quality)
        
        content = buffer.getvalue()
        file_extension = 'jpg'
    
    return content, file_extension

def main():
    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    cur = conn.cursor()
    
    print("Connecting to MinIO...")
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    
    # Ensure bucket exists
    bucket_name = "healthstash-files"
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
        print(f"Created bucket: {bucket_name}")
    
    # Get or create a test user
    cur.execute("SELECT id FROM users LIMIT 1")
    user_result = cur.fetchone()
    
    if user_result:
        user_id = user_result[0]
        print(f"Using existing user: {user_id}")
    else:
        # Create a test user
        user_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO users (id, email, full_name, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, "test@healthstash.local", "Test User", True, 
              datetime.datetime.utcnow(), datetime.datetime.utcnow()))
        conn.commit()
        print(f"Created test user: {user_id}")
    
    print("\nGenerating 64 sample health records...")
    
    for i in range(64):
        record_id = str(uuid.uuid4())
        record_type = random.choice(RECORD_TYPES)
        record_date = fake.date_between(start_date='-2y', end_date='today')
        
        # Generate file with size between 1-3 MB
        file_size_mb = random.uniform(1, 3)
        file_content, file_extension = create_sample_file(record_type, file_size_mb)
        
        # Upload to MinIO
        file_id = uuid.uuid4().hex[:16]
        file_name = f"{file_id}.{file_extension}"
        file_path = f"{user_id}/{file_name}"
        
        minio_client.put_object(
            bucket_name,
            file_path,
            io.BytesIO(file_content),
            len(file_content),
            content_type='application/pdf' if file_extension == 'pdf' else 'image/jpeg'
        )
        
        # Prepare record data
        title = f"{record_type} - {fake.date()}"
        description = f"{record_type} for {fake.text(max_nb_chars=100)}"
        provider = f"Dr. {fake.last_name()}, {random.choice(['MD', 'DO', 'PhD', 'DDS'])}"
        facility = f"{fake.company()} Medical Center"
        
        # Random body parts and categories
        body_parts = random.sample(BODY_PARTS, k=random.randint(1, 3))
        categories = random.sample(CATEGORIES, k=random.randint(1, 2))
        
        # Metadata
        metadata = {
            "test_results": {
                "summary": fake.text(max_nb_chars=200),
                "values": {
                    "param1": random.uniform(0, 100),
                    "param2": random.uniform(0, 200),
                    "status": random.choice(["Normal", "Abnormal", "Borderline"])
                }
            },
            "notes": fake.text(max_nb_chars=150),
            "follow_up": fake.date_between(start_date='today', end_date='+6m').isoformat()
        }
        
        # Map record type to category enum (using actual database enum values)
        category_map = {
            'Lab Results': 'lab_results',
            'X-Ray': 'imaging', 
            'MRI Scan': 'imaging',
            'CT Scan': 'imaging',
            'Prescription': 'prescriptions',
            'Vaccination Record': 'vaccinations',
            'Surgery Report': 'clinical_notes',
            'Consultation Notes': 'clinical_notes',
            'Blood Test': 'lab_results',
            'ECG Report': 'vital_signs',
            'Ultrasound': 'imaging',
            'Pathology Report': 'lab_results',
            'Discharge Summary': 'clinical_notes',
            'Referral Letter': 'clinical_notes',
            'Medical Certificate': 'other',
            'Allergy Test': 'lab_results',
            'Vision Test': 'clinical_notes',
            'Hearing Test': 'clinical_notes',
            'Dental Records': 'clinical_notes',
            'Physical Therapy': 'clinical_notes',
            'Mental Health Assessment': 'clinical_notes',
            'Cardiology Report': 'clinical_notes'
        }
        
        category = category_map.get(record_type, 'other')
        
        # Insert into database with correct column names
        cur.execute("""
            INSERT INTO health_records (
                id, user_id, category, service_date, title, description,
                provider_name, file_name, minio_object_name, file_size, file_type,
                categories, metadata_json, body_parts,
                location, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            record_id, user_id, category, record_date, title, description,
            provider, file_name, file_path, len(file_content), file_extension,
            ','.join(categories), json.dumps(metadata), ','.join(body_parts), 
            random.choice(['home', 'hospital', 'clinic', 'lab']),
            datetime.datetime.utcnow(), datetime.datetime.utcnow()
        ))
        
        if (i + 1) % 10 == 0:
            conn.commit()
            print(f"Created {i + 1}/64 records...")
    
    conn.commit()
    print("\n✅ Successfully generated 64 sample health records with files!")
    
    # Show statistics
    cur.execute("""
        SELECT 
            COUNT(*) as total_records,
            COALESCE(SUM(file_size), 0) / (1024.0 * 1024.0) as total_size_mb,
            COALESCE(AVG(file_size), 0) / (1024.0 * 1024.0) as avg_size_mb
        FROM health_records
        WHERE user_id = %s
    """, (user_id,))
    
    stats = cur.fetchone()
    print(f"\nStatistics:")
    print(f"  Total records: {stats[0]}")
    print(f"  Total size: {stats[1]:.2f} MB")
    print(f"  Average file size: {stats[2]:.2f} MB")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()