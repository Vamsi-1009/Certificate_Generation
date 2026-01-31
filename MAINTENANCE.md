# Maintenance Guide - Certificate Generation

## Updating the Template
If the college changes the certificate design:
1. Replace 'templates/certificate_template.jpg'.
2. Update 'config.py' with the new (x, y) coordinates in 'POSITIONS'.

## Troubleshooting
- **Path Errors**: Always run scripts from the root directory using 'python -m' or setting 'PYTHONPATH'.
- **Photo Issues**: Ensure student photos in 'student_data/photos/' match the filenames in 'students.csv'.
