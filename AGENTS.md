# PlanYourMeals Agent — Project Context for Claude Agents

## Mission

Rebuild **planyourmeals.com** as a modern, agent-powered meal planning service. The core interaction model shifts from a traditional form-based UI to a **conversational AI agent** that helps users plan meals, hit nutritional targets, discover recipes, and generate shopping lists — all through natural language.

The system is built on **AWS AgentCore** running a **LangGraph** agent that orchestrates tool calls against backend services derived from two legacy codebases.

---

## Repository Structure (Target Monorepo)

```
planyourmeals_agent/
├── AGENTS.md                    # This file — project context for Claude agents
├── agent/                       # LangGraph agent definition
│   ├── graph.py                 # Agent graph definition (nodes, edges, state)
│   ├── state.py                 # Agent state schema
│   ├── tools/                   # Tool definitions the agent can call
│   │   ├── meal_plan.py         # Autoplan, adjust, alternatives
│   │   ├── food_search.py       # Food/recipe search
│   │   ├── nutrition.py         # Nutrient requirements, tracking
│   │   ├── menu.py              # Menu management (browse, clone, edit)
│   │   ├── shopping_list.py     # Shopping list generation
│   │   ├── user.py              # User profile, preferences, onboarding
│   │   └── recipe.py            # Recipe CRUD
│   ├── prompts/                 # System prompts and prompt templates
│   └── config.py                # Agent configuration
├── api/                         # Backend API (derived from legacy Django app)
│   ├── app/                     # Django project (modernized)
│   │   ├── core/                # Users, profiles, menus, preferences
│   │   ├── food/                # Food database, recipes, tags
│   │   ├── plan/                # Meal plans, shopping lists
│   │   └── autoplanner/         # Pyomo/CBC meal plan optimizer
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
├── web/                         # Frontend (new — replaces legacy React app)
│   ├── src/
│   │   ├── app/                 # Next.js app router pages
│   │   ├── components/          # UI components
│   │   │   ├── chat/            # Chat interface for agent interaction
│   │   │   ├── plan/            # Meal plan display (cards, calendar)
│   │   │   ├── landing/         # Landing page & marketing
│   │   │   └── common/          # Shared components (nav, auth, layout)
│   │   └── lib/                 # Client utilities, API client, auth
│   ├── package.json
│   ├── Dockerfile
│   └── next.config.js
├── infra/                       # Infrastructure as Code
│   ├── terraform/               # Terraform modules
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── networking.tf        # VPC, subnets, security groups
│   │   ├── ecs.tf               # ECS Fargate for API + web
│   │   ├── rds.tf               # PostgreSQL database
│   │   ├── agentcore.tf         # AWS AgentCore configuration
│   │   ├── cloudfront.tf        # CDN + domain routing
│   │   ├── route53.tf           # DNS (planyourmeals.com)
│   │   ├── s3.tf                # Media storage
│   │   ├── ses.tf               # Email
│   │   └── outputs.tf
│   └── environments/
│       ├── dev.tfvars
│       └── prod.tfvars
├── docker-compose.yml           # Local development environment
└── .github/
    └── workflows/
        ├── deploy-api.yml
        ├── deploy-web.yml
        └── deploy-agent.yml
```

---

## Legacy Codebases

This project combines and modernizes two existing repositories:

### 1. planyourmealsapi (Django REST Backend)

**Repo:** `github.com/jamesdvance/planyourmealsapi` (branch: `master`)

**Stack:** Django 2.0, Django REST Framework 3.10, PostgreSQL (AWS RDS), Celery + RabbitMQ, Pyomo/CBC solver, AWS S3/SES, Stripe

**Key apps:**

| App | Purpose | Key Models |
|-----|---------|------------|
| `core/` | Users, profiles, menus, nutrient preferences | `Profile`, `UserMenu`, `PrefMenu`, `FoodPreferences`, `UserProbRejectFood`, `UserAccount` |
| `food/` | Food database, recipes, tags | `Foods` (full nutritional data for 15+ nutrients), `Recipes`, `RecipeFood`, `FoodTags`, `FoodIndex` |
| `plan/` | Meal plans, shopping lists | `Meal`, `PlanMeal` (user+meal_type+date), `Food_Amount` |
| `autoplanner/` | Mathematical meal plan optimization | `WeekAutoPlanner` (Pyomo CBC), `AmountAdjuster`, `AlternativesEngine` |

**Critical domain logic to preserve:**
- **WeekAutoPlanner** (`autoplanner/autoplan_week.py`): Mixed-integer optimization model that generates weekly meal plans meeting nutritional constraints. This is the core differentiator — it takes user food preferences, nutritional requirements (with upper/lower bounds for 15 nutrients), and probability/rejection scores, then solves for an optimal week of meals.
- **Nutrient system**: Users set requirements for calories, protein, carbs, fat, fiber, sugar, saturated fat, cholesterol, sodium, potassium, calcium, iron, vitamin A, vitamin C, vitamin D — each with min/max bounds and toggleable tracking.
- **Menu system**: Hierarchical — PublicMenu → UserMenu → PrefMenu (per meal type) → FoodPreferences. Users clone public menus, then customize which foods appear in each meal slot.
- **Probability/rejection scoring**: Both global and per-user scores track how often foods are used, viewed, removed, and rated. These scores feed into the optimizer to personalize recommendations over time.

**API endpoints** the agent tools will call (or whose logic will be extracted):
- `autoplan/autoplan_week/` — Generate optimized weekly meal plan
- `autoplan/auto_adjust_week/` — Adjust food amounts to hit nutrient targets
- `autoplan/get_food_alternative/` — Suggest food swaps
- `plan/get_day_plan/`, `plan/get_range_plan/` — Retrieve meal plans
- `plan/save_meal/`, `plan/edit_meal/` — Meal CRUD
- `plan/get_shopping_list_from_plan/` — Shopping list generation
- `search/food/`, `search/meals/` — Search
- `core/update_nutrient/`, `core/get_user_nut_reqs/` — Nutrient requirements
- `core/add_menu_item/`, `core/remove_menu_item/` — Menu management
- `food/save_recipe/`, `food/edit_recipe/` — Recipe CRUD

**Database:** PostgreSQL on AWS RDS. The `Foods` table is the largest and most critical — it contains the USDA food database plus user-created foods/recipes, each with full nutritional breakdowns. The `FoodIndex` table stores nutrient-per-calorie ratios used by the optimizer.

### 2. planyourmeals_react (React Frontend)

**Repo:** `github.com/jamesdvance/planyourmeals_react` (branch: `master`)

**Stack:** React 16.9, Redux + redux-thunk, Material-UI 4, Axios, Stripe.js, react-router-dom

**Key pages and features (for reference — the new frontend will be rebuilt from scratch):**

| Feature Area | What It Does |
|-------------|--------------|
| **7-day meal planner** | Calendar-style grid: 7 days × 4 meal types (breakfast/lunch/dinner/snack). Each cell contains food items with amounts. Shows per-day and per-meal nutrient totals. |
| **Autoplan** | One-click weekly meal plan generation. Results populate the 7-day grid. Users can swap individual foods (alternatives), undo/redo, and re-adjust amounts. |
| **Nutrient dashboard** | Table of 15 nutrients with current values vs requirements, upper/lower bounds, and toggle switches. Color-coded status (under/met/over). |
| **Food search** | Autocomplete search across the food database. Returns foods with nutritional info. |
| **Menu browser** | Browse/clone public menus. Edit personal menus by adding/removing foods per meal type. |
| **Recipe input** | Form to create recipes with ingredients (food search + amounts), instructions, cook time, image upload. |
| **Shopping list** | Generated from a date range of meal plans. Aggregated ingredients. |
| **Onboarding** | First-time user flow: choose a starter menu → set physical stats → set nutritional goals. |
| **Auth** | Email/password signup + login, Google OAuth, Facebook OAuth, password reset. |
| **Account/Payments** | Stripe subscription management (trial → free → paid). |

**Redux state shape** (important for understanding the data model from the frontend perspective):
- `columns`: 7-day plan with undo/redo. Each day has 4 meal types, each with `foods_list` (array of food objects with amounts and nutrients) and `nutrient_totals`.
- `user`: Nutrient requirements (list + dict), menus, calorie/macro targets, display preferences, account status.
- `auth`: Token-based authentication state.

---

## Architecture Decisions

### Agent Architecture: AWS AgentCore + LangGraph

The agent is the primary user-facing interface. Users interact via a chat UI on the landing page. The agent:

1. **Understands user goals** — "I want to eat 2000 calories with high protein", "Plan my meals for the week", "I'm vegetarian", "What can I substitute for chicken?"
2. **Calls tools** to execute actions against the backend API
3. **Presents results** in a rich, structured format (meal plan cards, nutrient summaries, shopping lists)
4. **Maintains conversation context** to refine plans iteratively

**LangGraph** is used to define the agent's control flow as a graph with:
- **Nodes**: LLM reasoning, tool execution, response formatting
- **State**: Conversation history, current user context (profile, active plan, preferences), tool results
- **Edges**: Conditional routing based on user intent and tool outcomes

**AWS AgentCore** provides:
- Managed agent runtime and scaling
- Built-in memory/session management
- Tool orchestration
- Observability and tracing

### Agent Tools

Each tool wraps a set of related backend API operations. Tools should:
- Accept structured inputs (validated with Pydantic models)
- Return structured outputs the agent can reason about
- Handle errors gracefully with informative messages
- Be idempotent where possible

**Tool categories:**

| Tool | Operations | Source Logic |
|------|-----------|--------------|
| `meal_plan` | Generate weekly plan, adjust amounts, get day/range plan, clear meals | `autoplanner/`, `plan/views.py` |
| `food_search` | Search foods, search meals, get food details | `food/views.py`, `plan/views.py` |
| `nutrition` | Get/set nutrient requirements, get nutrient summary for a plan | `core/views.py` |
| `menu` | Browse public menus, clone menu, add/remove foods from menu | `core/views.py` |
| `shopping_list` | Generate shopping list from date range | `plan/views.py` |
| `user` | Get/update profile, set dietary preferences, onboarding | `core/views.py` |
| `recipe` | Create/edit recipes, search user recipes | `food/views.py` |
| `food_alternative` | Get alternative foods for a meal plan item | `autoplanner/alternatives_engine.py` |

### Frontend: New Build with Next.js

The frontend is rebuilt from scratch using a modern stack. It is **not** a port of the legacy React app — it's a new design centered around the agent chat experience.

**Stack:** Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui components

**Key pages:**

| Route | Purpose |
|-------|---------|
| `/` | Landing page — hero section, feature highlights, CTA to try the agent |
| `/chat` | Main agent chat interface (authenticated). Rich message rendering for meal plans, nutrient charts, shopping lists. |
| `/plan` | Visual meal plan view (populated by agent, also directly browsable). 7-day calendar grid. |
| `/login`, `/signup` | Authentication |
| `/account` | Account management, subscription |

**Design principles:**
- **Chat-first**: The chat interface is the primary way users interact. The plan view is a companion display that updates as the agent makes changes.
- **Responsive**: Mobile-first design. Chat works well on phones.
- **Fast**: Server-side rendering for landing page (SEO). Client-side for authenticated app.
- **Accessible**: Follow WCAG 2.1 AA guidelines.

### Backend: Modernized Django

The Django backend is modernized but preserves the core domain logic:

- **Upgrade** to Django 4.2+ and Python 3.11+
- **Containerize** with Docker
- **Keep** the Pyomo/CBC autoplanner, nutrient system, food database, menu system
- **Remove** Celery/RabbitMQ dependency initially (replace scheduled tasks with simpler solutions or AWS-native services)
- **Remove** Stripe integration initially (re-add later)
- **Remove** social auth initially (start with email/password, add OAuth later)
- **Add** proper API documentation (OpenAPI/Swagger)
- **Fix** hardcoded credentials → environment variables
- **Fix** raw SQL queries → Django ORM where possible
- **Add** proper test coverage

### Infrastructure: Terraform on AWS

All infrastructure is managed via Terraform. The target architecture:

```
                         ┌─────────────────┐
                         │   Route 53      │
                         │ planyourmeals.com│
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │   CloudFront    │
                         │   Distribution  │
                         └───┬─────────┬───┘
                             │         │
                    ┌────────▼──┐  ┌───▼────────┐
                    │  Next.js  │  │  Django API │
                    │  (ECS     │  │  (ECS       │
                    │  Fargate) │  │  Fargate)   │
                    └───────────┘  └──────┬──────┘
                                          │
                              ┌───────────▼──────────┐
                              │   AWS AgentCore      │
                              │   (LangGraph Agent)  │
                              └───────────┬──────────┘
                                          │
                    ┌─────────┬───────────┼───────────┐
                    │         │           │           │
               ┌────▼───┐ ┌──▼───┐  ┌────▼───┐ ┌────▼───┐
               │  RDS   │ │  S3  │  │  SES   │ │Bedrock │
               │Postgres│ │Media │  │ Email  │ │  LLM   │
               └────────┘ └──────┘  └────────┘ └────────┘
```

**Domain routing:**
- `planyourmeals.com` → CloudFront → Next.js (ECS Fargate)
- `api.planyourmeals.com` → CloudFront → Django API (ECS Fargate)
- The domain is already active and pointed at an S3 bucket. Migration to CloudFront needs to be handled carefully with zero-downtime DNS cutover.

**Key infrastructure components:**
- **VPC** with public/private subnets across 2 AZs
- **ECS Fargate** for both web and API containers (no EC2 management)
- **RDS PostgreSQL** (existing database to migrate or connect to)
- **S3** for media storage (existing bucket: `planyourmealsmedia`)
- **SES** for transactional email
- **CloudFront** for CDN and HTTPS termination
- **Route 53** for DNS management
- **ECR** for container image registry
- **Secrets Manager** for credentials (database, API keys, etc.)
- **CloudWatch** for logging and monitoring

---

## Development Phases

### Phase 1: Foundation
- [ ] Set up monorepo structure with Docker Compose for local dev
- [ ] Port and modernize Django API (upgrade deps, containerize, env vars for secrets)
- [ ] Migrate the autoplanner and core models to the new repo
- [ ] Set up basic Terraform scaffolding (VPC, ECS cluster, RDS)
- [ ] Verify the food database and autoplanner work in the new environment

### Phase 2: Agent
- [ ] Define LangGraph agent graph (state, nodes, edges)
- [ ] Implement agent tools wrapping the Django API
- [ ] Set up AWS AgentCore deployment
- [ ] Build agent system prompt with meal planning domain knowledge
- [ ] Test agent with CLI before connecting frontend

### Phase 3: Frontend
- [ ] Build Next.js app with landing page
- [ ] Implement chat interface with streaming agent responses
- [ ] Build rich message components (meal plan cards, nutrient charts, food cards)
- [ ] Implement authentication (email/password)
- [ ] Connect chat to agent via WebSocket or SSE

### Phase 4: Infrastructure & Deployment
- [ ] Complete Terraform modules for all AWS resources
- [ ] Set up CI/CD pipelines (GitHub Actions)
- [ ] Deploy to staging environment
- [ ] Migrate DNS from S3 to CloudFront
- [ ] Production deployment

### Phase 5: Polish & Extend
- [ ] Add OAuth (Google, Facebook)
- [ ] Add Stripe subscription management
- [ ] Add meal plan visual view (calendar grid alongside chat)
- [ ] Add shopping list export (email, PDF)
- [ ] Performance optimization and caching

---

## Conventions & Standards

### Code Style
- **Python**: Follow PEP 8. Use type hints. Use `ruff` for linting and formatting.
- **TypeScript**: Follow ESLint + Prettier. Strict TypeScript (`strict: true`).
- **Terraform**: Follow HashiCorp style guide. Use consistent naming: `snake_case` for resources, descriptive names.

### Git
- **Branch naming**: `feature/description`, `fix/description`, `infra/description`
- **Commit messages**: Imperative mood, concise. E.g., "Add meal plan tool to agent", "Fix nutrient calculation in autoplanner"
- **PRs**: Always create PRs against `main`. Include description of changes and test plan.

### Secrets
- **Never** commit secrets, API keys, database credentials, or Stripe keys to the repo.
- Use environment variables locally (`.env` files in `.gitignore`).
- Use AWS Secrets Manager in production.
- The legacy repos have hardcoded credentials — these must NOT be carried over.

### Docker
- Each service (api, web) has its own Dockerfile.
- `docker-compose.yml` at repo root for local development with all services.
- Use multi-stage builds to keep images small.

### Testing
- **API**: pytest + Django test client. Test views, serializers, and the autoplanner.
- **Web**: Vitest + React Testing Library for components. Playwright for E2E.
- **Agent**: Test tool calls with mocked API responses. Integration tests with real backend.

---

## Key Technical Details

### Food Nutritional Data Schema

The `Foods` model has these nutritional fields (per serving):
- `calories`, `protein`, `carbohydrates`, `fat` (macros)
- `fiber`, `sugar`, `sat_fat`, `cholesterol` (secondary)
- `sodium`, `potassium`, `calcium`, `iron` (minerals)
- `vit_a`, `vit_c`, `vit_d` (vitamins)
- `serving_size`, `serving_unit`, `servings_per_container`

The `FoodIndex` model stores nutrient-per-calorie ratios used by the optimizer to quickly rank foods by nutrient density.

### Autoplanner Optimization Model

The `WeekAutoPlanner` builds a Pyomo `ConcreteModel` with:
- **Decision variables**: Binary selection of foods per meal slot, continuous serving amounts
- **Objective**: Maximize preference scores (probability of acceptance) while meeting nutrient constraints
- **Constraints**:
  - Nutrient upper/lower bounds per day
  - Max servings per food
  - Meal type restrictions (foods only appear in allowed meal types)
  - Variety constraints (limit repeats across the week)
- **Solver**: CBC (open-source mixed-integer programming solver)

This is computationally intensive and should run asynchronously. The agent should indicate to the user that plan generation is in progress and stream results when ready.

### User Onboarding Flow (Agent-Guided)

The agent should guide new users through:
1. **Dietary preferences** — "Do you have any dietary restrictions?" (vegetarian, vegan, gluten-free, allergies, etc.)
2. **Physical stats** (optional) — Age, sex, weight, height, activity level → auto-calculate TDEE and nutrient targets
3. **Menu selection** — "Here are some starter menus. Which sounds closest to how you like to eat?" → Clone a public menu
4. **First plan** — "Let me generate your first weekly meal plan!" → Run autoplanner → Present results

### Authentication

- Start with email/password using Django REST Framework tokens
- Token sent in `Authorization: Token <token>` header
- Frontend stores token in `localStorage` (consider `httpOnly` cookies for better security in the new version)

---

## Environment Variables

These environment variables must be configured (never hardcoded):

```env
# Database
DATABASE_HOST=
DATABASE_PORT=5432
DATABASE_NAME=plmapi
DATABASE_USER=
DATABASE_PASSWORD=

# Django
DJANGO_SECRET_KEY=
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=api.planyourmeals.com

# AWS
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1
AWS_S3_BUCKET=planyourmealsmedia

# Email (SES)
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Agent
ANTHROPIC_API_KEY=        # or AWS Bedrock credentials
AGENTCORE_ENDPOINT=

# Frontend
NEXT_PUBLIC_API_URL=https://api.planyourmeals.com
NEXT_PUBLIC_WS_URL=wss://api.planyourmeals.com/ws
```

---

## Reference: Legacy File Locations

When porting code from the legacy repos, here's where to find key logic:

| What | Legacy Location | New Location |
|------|----------------|-------------|
| Autoplanner optimizer | `planyourmealsapi/autoplanner/autoplan_week.py` | `api/app/autoplanner/autoplan_week.py` |
| Amount adjuster | `planyourmealsapi/autoplanner/adjust_amounts.py` | `api/app/autoplanner/adjust_amounts.py` |
| Alternatives engine | `planyourmealsapi/autoplanner/alternatives_engine.py` | `api/app/autoplanner/alternatives_engine.py` |
| Core models (Profile, Menu, etc.) | `planyourmealsapi/core/models.py` | `api/app/core/models.py` |
| Food models | `planyourmealsapi/food/models.py` | `api/app/food/models.py` |
| Plan models | `planyourmealsapi/plan/models.py` | `api/app/plan/models.py` |
| API views (core) | `planyourmealsapi/core/views.py` | `api/app/core/views.py` |
| API views (food) | `planyourmealsapi/food/views.py` | `api/app/food/views.py` |
| API views (plan) | `planyourmealsapi/plan/views.py` | `api/app/plan/views.py` |
| Django settings | `planyourmealsapi/planyourmeals_api/settings/base.py` | `api/app/config/settings/base.py` |
| URL routing | `planyourmealsapi/planyourmeals_api/urls.py` | `api/app/config/urls.py` |
| Redux initial state (data model reference) | `planyourmeals_react/planyourmeals/src/initialState.js` | Reference only — not ported |
| Redux actions (API call patterns) | `planyourmeals_react/planyourmeals/src/actions/*.js` | Reference only — rewritten as agent tools |
| Landing page design reference | `planyourmeals_react/planyourmeals/src/components/landing_page/` | `web/src/components/landing/` (new design) |
| Meal plan UI reference | `planyourmeals_react/planyourmeals/src/components/plan/` | `web/src/components/plan/` (new design) |
