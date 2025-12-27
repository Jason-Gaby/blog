# reset_database.ps1
# Script to reset SQLite database, run migrations, clear sites, and load fixture

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Database Reset and Fixture Load Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Delete existing database
Write-Host "[Step 1/4] Deleting existing database..." -ForegroundColor Yellow

$dbPath = ".\db.sqlite3"

if (Test-Path $dbPath) {
    try {
        Remove-Item $dbPath -Force
        Write-Host "✓ Database deleted successfully" -ForegroundColor Green
    } catch {
        Write-Host "✗ Error deleting database: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠ No existing database found (this is okay)" -ForegroundColor Gray
}

Write-Host ""

# Step 2: Run migrations
Write-Host "[Step 2/4] Running migrations..." -ForegroundColor Yellow

try {
    python manage.py migrate
    if ($LASTEXITCODE -ne 0) {
        throw "Migration failed with exit code $LASTEXITCODE"
    }
    Write-Host "✓ Migrations completed successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Error running migrations: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Delete all Site objects
Write-Host "[Step 3/4] Clearing existing Wagtail sites..." -ForegroundColor Yellow

$pythonCommand = @"
from wagtail.models import Site, Page
count = Site.objects.count()
Site.objects.all().delete()
print(f'Deleted {count} site(s)')

# Clear ALL pages (including root page created by migrations)
page_count = Page.objects.count()
Page.objects.all().delete()
print(f'Deleted {page_count} page(s) including root')

"@

try {
    $result = python manage.py shell -c $pythonCommand
    Write-Host "✓ $result" -ForegroundColor Green
} catch {
    Write-Host "✗ Error clearing sites: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 4: Sanitize JSON and Load Fixture
Write-Host "[Step 4/4] Sanitizing and Loading fixture..." -ForegroundColor Yellow

$fixturePath = ".\downloads\dev_data.json"

# This Python snippet removes the revision IDs from the JSON so the import doesn't crash
$sanitizeCommand = @"
import json
path = r'$fixturePath'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for obj in data:
    if obj['model'] == 'wagtailcore.page':
        # Remove the pointer to the non-existent revision
        if 'latest_revision' in obj['fields']:
            obj['fields']['latest_revision'] = None
        if 'live_revision' in obj['fields']:
            obj['fields']['live_revision'] = None

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)
"@

try {
    python -c $sanitizeCommand
    Write-Host "✓ JSON sanitized (Revision pointers removed)" -ForegroundColor Green

    python manage.py loaddata $fixturePath
    Write-Host "✓ Fixture loaded successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Error during load: $_" -ForegroundColor Red
    exit 1
}



Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Database reset complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now run:" -ForegroundColor White
Write-Host "  python manage.py runserver" -ForegroundColor Cyan
Write-Host ""