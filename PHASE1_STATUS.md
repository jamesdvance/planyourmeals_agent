# Phase 1 Status — Last Updated 2026-02-08

## Current Step: Step 8 (First Boot)

Steps 1-7 and 9-14 are fully implemented and committed. We are blocked on
Step 8 (first boot) because Docker Desktop on Windows requires WSL2, which
conflicts with the dual-boot Ubuntu setup. **Continue from Step 8 on Ubuntu.**

---

## What's Been Completed

### Step 0: Install Local Tooling (PARTIAL)
- [x] Python 3.13.12 installed on Windows (`C:/Users/james/AppData/Local/Programs/Python/Python313/`)
- [x] Docker Desktop 29.2.0 installed on Windows (but cannot start — needs WSL2)
- [ ] **On Ubuntu: install Python 3.13, Docker, docker-compose, gh CLI**
- [ ] Node.js (not needed until Phase 2 frontend work)

### Step 1: Repo Scaffolding ✅
- `.gitignore` with Python/Node/Terraform/Docker/IDE rules
- Directory tree: `_legacy/`, `api/`, `web/`, `agent/`, `infra/`, `.github/workflows/`
- Stale files removed (`nul`, `api_tree.json`, `react_tree.json`)
- Commit: `7dff7d6`

### Step 2: Legacy Subtree Import ✅
- `_legacy/api/` imported from `github.com/jamesdvance/planyourmealsapi.git` (squashed)
- React repo skipped (358MB node_modules committed in legacy — reference on GitHub instead)
- Commit: via `git subtree add`

### Step 3: Docker + Dockerfile ✅
Files created:
- `docker-compose.yml` — PostgreSQL 16 (`db`) + Django API (`api`), health checks, volume mounts
- `api/Dockerfile` — `python:3.13-slim`, installs `coinor-cbc` + `libpq-dev`, pip install
- `api/requirements.txt` — Django 5.1.5, DRF 3.15.2, Pyomo 6.8.2, psycopg 3.2.4, etc.
- `api/.env.example` and `api/.env` (local dev credentials, gitignored)

### Step 4: Django 5 Project Skeleton ✅
Files created:
- `api/manage.py` (DJANGO_SETTINGS_MODULE = `app.config.settings.base`)
- `api/app/config/settings/base.py` — all secrets via `python-decouple`, INSTALLED_APPS includes
  rest_framework, corsheaders, app.core, app.food, app.plan
- `api/app/config/urls.py` — versioned prefixes: `api/v1/core/`, `api/v1/food/`, `api/v1/plan/`, `api/v1/autoplan/`
- `api/app/config/wsgi.py`
- `__init__.py` files for all packages
- `apps.py` for each app (core, food, plan)

### Step 5: Core Models ✅
File: `api/app/core/models.py` (322 lines)

Models ported from `_legacy/api/core/models.py`:
- **Profile** — 1:1 with User. Physical stats + 15 nutrients × 3 fields (track flag, upper bound,
  lower bound). All defaults match legacy. `db_table = "core_profile"`.
- **PublicMenu** — Curated menu templates with FK to 4 PrefMenus
- **UserMenu** — User's menu (may be cloned from PublicMenu)
- **PrefMenu** — Per-meal-type preferences (breakfast/lunch/dinner/snack)
- **FoodPreferences** — Links a Food to a PrefMenu for a meal type + dish category
- **UserProbRejectFood** — Per-user food scoring (viewed, removed, uses, rating, last_view/use).
  Includes `prob_r` property matching legacy formula.

Legacy models **NOT ported** (deferred or unnecessary):
- PersonalProfile, FoodDishes, MenuTags, TaggedMenus (not used by autoplanner)
- MealPreferences, RestaurantPreferences, FoodTagPreferences, MealTagPreferences
  (simplified — autoplanner query was updated to work with FoodPreferences only)
- GlobalProbRejectFood/Meal, UserProbRejectMeal (deferred)
- ExcludeFoods/Meals, ViewedToday (deferred)
- UserAccount, UserMessage, Blog, NutrientInfo, ProbRejectCoefficients (deferred)

### Step 6: Food Models ✅
File: `api/app/food/models.py` (179 lines)

- **Food** — Name, brand, 15 nutrient fields, serving info, is_recipe flag, created_by.
  Indexes on food_description and (is_recipe, created_by). `db_table = "food_foods"`.
- **FoodTag** — Tag name (unique). `db_table = "food_foodtags"`.
- **FoodTagMapping** — Through table. `db_table = "food_taggedfoods"`.
- **FoodIndex** — 1:1 with Food. 12 nutrient-per-calorie ratio fields. `db_table = "food_foodindex"`.
- **Recipe** — 1:1 with Food. Instructions (JSONField), cook/prep time, servings.
- **RecipeFood** — Ingredient in a recipe (food FK + amount + unit).

Key change from legacy: `food_key` (manual integer PK) replaced with Django auto-increment `id`.
All raw SQL in the autoplanner updated to use `f.id` instead of `f.food_key`.

### Step 7: Plan Models ✅
File: `api/app/plan/models.py` (86 lines)

- **Meal** — User's meal collection. `db_table = "plan_meal"`.
- **FoodAmount** — Food in a meal with serving amount. `db_table = "plan_food_amount"`.
- **PlanMeal** — Places a Meal in a date+meal_type slot. UniqueConstraint on
  (user, plan_date, meal_type). `db_table = "plan_planmeal"`.

### Step 8: First Boot ❌ BLOCKED — DO THIS ON UBUNTU
Commands to run:
```bash
cd planyourmeals_agent
docker compose up --build -d
docker compose exec api python manage.py makemigrations core food plan
docker compose exec api python manage.py migrate
docker compose exec api python manage.py load_seed_foods
docker compose exec api python manage.py create_test_user
docker compose exec api python manage.py createsuperuser
```
Verify: Django admin at `http://localhost:8000/admin/`, all models visible, 50 seed foods loaded.

### Step 9: Autoplanner ✅
Files created in `api/app/autoplanner/`:

**autoplan_week.py** (~500 lines)
- `WeekAutoPlanner` class with `solve()` → returns `PlanResult` dataclass
- Preserves Pyomo ConcreteModel structure: binary `ind` vars, integer `amt` vars,
  Big-M linking, GDP disjunction for standalone vs by-dish meal selection
- Raw SQL queries updated: `f.food_key` → `f.id`, table names match `db_table` values
- Uses `django.db.connection` instead of raw psycopg2 connection
- Named constants extracted (PROB_R weights, SOLVER_NAME, etc.)
- `_prep_query_params()`, `_build_opt_dataset()`, `_set_opt_variables()`,
  `_build_model()`, `_solve_model()`, `_parse_results()`

**adjust_amounts.py** (~200 lines)
- `AmountAdjuster` class — adjusts serving amounts for a single day
- Same Pyomo pattern: ConcreteModel, nutrient constraints, prob_r objective

**alternatives_engine.py** (~170 lines)
- `AlternativesEngine` class — finds food alternatives and similar foods
- Brute-force solver (no_opt_solve) + greedy nutrient-index distance

**views.py** — Thin DRF views calling service classes
**urls.py** — `autoplan_week/` and `get_food_alternative/` endpoints

**Simplifications from legacy:**
- Removed pandas `.append()` (deprecated) → replaced with `pd.concat()`
- Removed `pyutilib` signal handler hack (not needed in modern Pyomo)
- Removed hardcoded solver path — uses `SolverFactory("cbc")` which finds it on PATH
- Removed restaurant/meal-as-food queries from the main SQL (simplified to food preferences + tags only)
- The `resolve_weekplan`, `solve_again_weekplan`, `solve_and_return_all_weekplans` methods
  were not ported yet (they're variations of the main solve — can be added in Phase 2)

### Step 10: Seed Data ✅
- `api/app/food/management/commands/load_seed_foods.py` — 50 representative foods with
  realistic nutritional data (proteins, grains, vegetables, fruits, dairy, snacks).
  Creates FoodIndex records for each. Assigns 5 tags (high-protein, vegetarian, low-carb,
  gluten-free, quick-prep).
- `api/app/core/management/commands/create_test_user.py` — Creates testuser@example.com
  with Profile, 4 PrefMenus, UserMenu, and FoodPreferences assigned by keyword matching.

### Step 11: API Views + Serializers ✅
Endpoints implemented:
- `GET /api/v1/core/profile/` — User profile + all nutrient fields
- `PUT /api/v1/core/profile/nutrients/` — Update nutrient flags and bounds
- `GET /api/v1/food/search/?q=` — Food search using raw SQL with ILIKE
- `GET /api/v1/food/{id}/` — Food detail via DRF ModelSerializer
- `GET /api/v1/plan/day/{date}/` — Day plan with nested meal + food amounts
- `POST /api/v1/autoplan/autoplan_week/` — Generate weekly plan (calls WeekAutoPlanner)
- `POST /api/v1/autoplan/get_food_alternative/` — Get alternatives (calls AlternativesEngine)

All views require `IsAuthenticated`. No auth system configured yet (Phase 2).

### Step 12: Tests ✅
- `api/pytest.ini` — DJANGO_SETTINGS_MODULE configured
- `api/tests/conftest.py` — Fixtures: user, profile, sample_food, sample_foods (8 foods
  with FoodIndex), user_with_menus (full PrefMenu + FoodPreferences setup)
- `api/tests/test_models.py` — Food CRUD, FoodIndex, tags, recipes, Profile, PrefMenu,
  FoodPreferences, UserMenu, UserProbRejectFood, Meal, FoodAmount, PlanMeal unique constraint
- `api/tests/test_autoplanner.py` — prep_query_params test, full solve integration test
  (with relaxed bounds to ensure feasibility with small food set)
- `api/tests/test_api.py` — Profile GET/PUT, food search/detail, day plan empty/populated,
  invalid date handling

### Step 13: Terraform ✅
Files in `infra/terraform/`:
- `main.tf` — AWS provider, S3 backend (`planyourmeals-terraform-state`), DynamoDB lock table
- `variables.tf` — project_name, environment, VPC CIDR, DB credentials (sensitive), instance sizes
- `networking.tf` — VPC 10.0.0.0/16, 2 public + 2 private subnets, IGW, NAT gateway, route tables
- `rds.tf` — PostgreSQL 16, db.t3.micro, private subnet, SG allowing 5432 from VPC only
- `ecs.tf` — Fargate cluster, ECR repository (`planyourmeals-dev-api`), ECS tasks SG
- `outputs.tf` — VPC ID, subnet IDs, RDS endpoint, ECR URL, cluster ID
- `infra/environments/dev.tfvars` — Dev values (DB credentials via TF_VAR_ env vars)

### Step 14: GitHub Actions CI ✅
File: `.github/workflows/ci.yml`
- **lint** job: ruff check + ruff format --check
- **test** job: PostgreSQL 16 service container, installs coinor-cbc, runs pytest

---

## Git Log
```
c984ab0 Phase 1: Django API, Docker, autoplanner, Terraform, CI (62 files, +4031 lines)
<subtree> Squashed '_legacy/api/' content from planyourmealsapi master
7dff7d6 Initial scaffolding: monorepo structure, .gitignore, AGENTS.md
```

---

## What to Do on Ubuntu

### 1. Get the repo
If the repo is on a shared drive accessible from Ubuntu:
```bash
cd /path/to/planyourmeals_agent
```
Or push to GitHub first (from Windows):
```bash
git remote add origin https://github.com/jamesdvance/planyourmeals_agent.git
git push -u origin main
```
Then clone on Ubuntu:
```bash
git clone https://github.com/jamesdvance/planyourmeals_agent.git
cd planyourmeals_agent
```

### 2. Install dependencies on Ubuntu
```bash
# Python 3.13
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-dev

# Docker
sudo apt install docker.io docker-compose-v2
sudo usermod -aG docker $USER
# Log out and back in for group to take effect

# CBC solver (for running autoplanner outside Docker)
sudo apt install coinor-cbc

# GitHub CLI (optional)
sudo apt install gh
```

### 3. Create the .env file
```bash
cp api/.env.example api/.env
# Edit if needed — defaults work for local Docker dev
```

### 4. First Boot (Step 8)
```bash
docker compose up --build -d

# Wait for db health check to pass
docker compose ps

# Run migrations
docker compose exec api python manage.py makemigrations core food plan
docker compose exec api python manage.py migrate

# Load seed data
docker compose exec api python manage.py load_seed_foods
docker compose exec api python manage.py create_test_user

# Create admin superuser (interactive)
docker compose exec api python manage.py createsuperuser
```

### 5. Verify
- Django admin: http://localhost:8000/admin/ — all models should be visible
- Seed data: 50 foods, 5 tags, 1 test user with menus
- API: `curl -u admin:yourpassword http://localhost:8000/api/v1/food/search/?q=chicken`

### 6. Run Tests
```bash
docker compose exec api pytest -v
```

### 7. Run Ruff Lint
```bash
docker compose exec api ruff check .
docker compose exec api ruff format --check .
```

### 8. Autoplanner Verification (Key Milestone)
After seed data is loaded, test the autoplanner in Django shell:
```bash
docker compose exec api python manage.py shell
```
```python
import datetime
from django.contrib.auth.models import User
from app.core.models import UserMenu, Profile
from app.autoplanner.autoplan_week import WeekAutoPlanner

user = User.objects.get(username="testuser@example.com")
profile = user.profile
user_menu = UserMenu.objects.filter(user=user).first()

# Build requirements dict from profile bounds
requirements = {
    "day1": {
        "calories": [float(profile.cal_ub), float(profile.cal_lb)],
        "protein_g": [float(profile.pro_ub), float(profile.pro_lb)],
        "fat_g": [float(profile.fat_ub), float(profile.fat_lb)],
        "carb_g": [float(profile.car_ub), float(profile.car_lb)],
    }
}

menus_list = [{
    "day": "day1",
    "meals": [
        {"meal": "Breakfast", "menus": [{"type": "menu", "id": user_menu.breakfast_prefmenu_id}]},
        {"meal": "Lunch", "menus": [{"type": "menu", "id": user_menu.lunch_prefmenu_id}]},
        {"meal": "Dinner", "menus": [{"type": "menu", "id": user_menu.dinner_prefmenu_id}]},
        {"meal": "Snack", "menus": [{"type": "menu", "id": user_menu.snack_prefmenu_id}]},
    ]
}]

planner = WeekAutoPlanner(
    user_id=user.id,
    requirements_dict=requirements,
    menus_dict_list=menus_list,
    week_start_dt=datetime.date.today(),
    week_end_dt=datetime.date.today() + datetime.timedelta(days=7),
    n_snack=2,
)

result = planner.solve()
print(f"Status: {result.status}")
print(f"Solve time: {result.solve_time_seconds:.2f}s")
if not result.results_df.empty:
    print(result.results_df[["unique_id", "day", "meal", "dish_num", "amt"]])
```

If status is "optimal" with food selections, Phase 1 is complete.

---

## Known Issues / Things to Watch

1. **Windows Store Python alias** — On Windows, the Store alias intercepts `python`.
   Use full path or disable in Settings > Apps > App Execution Aliases.

2. **Autoplanner SQL simplification** — The legacy query had 6 UNION blocks covering
   menus, food prefs, restaurant prefs, tag prefs, standalone tags, and standalone
   restaurants. The new version only has food preferences + standalone tags (2 blocks).
   This means restaurant-based and meal-based preferences aren't queried yet. Those
   models were deferred from Step 5. When those models are added, the SQL should be
   extended to match.

3. **Authentication** — All API views require `IsAuthenticated` but no auth backend
   is configured beyond Django session auth. Phase 2 will add token auth or JWT.

4. **Pandas dependency** — The autoplanner uses pandas + numpy heavily (legacy pattern).
   This is fine for now but adds container size. A future optimization could replace
   pandas DataFrames with raw dicts/lists where possible.

5. **Ruff formatting** — The code was written to be ruff-clean, but hasn't been verified
   with `ruff check` and `ruff format` yet. Run these on first boot and fix any issues.
