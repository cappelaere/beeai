# RealtyIQ Test Suite

Comprehensive test suite for the RealtyIQ Agent UI application, covering backend API tests, frontend JavaScript tests, and end-to-end user flow tests.

## Test Structure

```
tests/
├── agent_app/tests/          # Django backend tests
│   ├── test_api.py           # API endpoint tests
│   └── test_models.py        # Model tests
├── frontend/                 # Frontend JavaScript unit tests
│   ├── test_chat.spec.js
│   ├── test_autocomplete.spec.js
│   ├── test_prompt_history.spec.js
│   └── test_theme.spec.js
├── e2e/                      # End-to-end tests
│   └── test_user_flows.spec.js
├── package.json              # Node.js dependencies
├── playwright.config.js      # Playwright configuration
└── README.md                 # This file
```

## Running Tests

### Backend Tests (Django)

Run all Django tests:
```bash
cd agent_ui
python manage.py test agent_app.tests
```

Run specific test file:
```bash
python manage.py test agent_app.tests.test_api
```

Run specific test class:
```bash
python manage.py test agent_app.tests.test_api.ChatAPITests
```

Run specific test method:
```bash
python manage.py test agent_app.tests.test_api.ChatAPITests.test_create_chat_session
```

With coverage:
```bash
coverage run --source='agent_app' manage.py test agent_app.tests
coverage report
coverage html  # Generate HTML report
```

### Frontend Unit Tests (Jest)

Install dependencies:
```bash
cd tests
npm install
```

Run all frontend tests:
```bash
npm test
```

Run tests in watch mode:
```bash
npm run test:watch
```

Run tests with coverage:
```bash
npm run test:coverage
```

### End-to-End Tests (Playwright)

Install Playwright browsers:
```bash
cd tests
npx playwright install
```

Run all E2E tests:
```bash
npm run test:e2e
```

Run E2E tests in headed mode (see browser):
```bash
npm run test:e2e:headed
```

Run E2E tests in debug mode:
```bash
npm run test:e2e:debug
```

Run specific test file:
```bash
npx playwright test e2e/test_user_flows.spec.js
```

Run specific test:
```bash
npx playwright test -g "user can send a message"
```

## Test Coverage

### Backend API Tests (`test_api.py`)

- **ChatAPITests**: Chat session creation, messaging, history retrieval
- **SessionAPITests**: Session management (create, list, rename, delete)
- **MessageFeedbackTests**: Thumbs up/down feedback submission
- **PromptSuggestionTests**: Autocomplete suggestions and ordering
- **PromptsManagementTests**: Prompts page CRUD operations, search, and filtering
- **PromptCardTests**: Favorite cards management
- **DocumentAPITests**: Document upload and management
- **DashboardAPITests**: Dashboard statistics and metrics
- **ViewTests**: Template rendering for all pages

### Backend Model Tests (`test_models.py`)

- **ChatSessionModelTests**: Session creation, defaults, ordering
- **ChatMessageModelTests**: Message creation, feedback, ordering
- **PromptCardModelTests**: Card creation, favorites, ordering
- **UploadedDocumentModelTests**: Document creation, ordering
- **PromptSuggestionModelTests**: Suggestion creation, uniqueness, ordering
- **ModelRelationshipTests**: Foreign key relationships, cascade deletes

### Frontend Unit Tests

- **test_chat.spec.js**: Chat UI, message rendering, copy, feedback, loading states
- **test_autocomplete.spec.js**: Autocomplete dropdown, suggestions, navigation
- **test_prompt_history.spec.js**: Readline-style history navigation
- **test_theme.spec.js**: Theme switching and persistence

### End-to-End Tests (`test_user_flows.spec.js`)

- **Chat Flow**: Send messages, receive responses, click favorite cards
- **Session Management**: Create, switch, delete sessions
- **Feedback**: Thumbs up/down on responses
- **Autocomplete**: Type to trigger suggestions, click to fill
- **Prompts Management**: View, search, filter, run, delete prompts
- **Dashboard**: View metrics and statistics
- **Theme Switching**: Toggle between light/dark/system themes
- **Copy Functionality**: Copy assistant responses
- **Voice Input**: Voice input button presence
- **Navbar Resize**: Horizontal navbar resizing
- **Panel Resize**: Vertical favorite cards panel resizing
- **Navigation**: Navigate between all pages

## Test Data Setup

### Seeding Test Data

Create prompt suggestions:
```bash
cd agent_ui
python manage.py seed_prompts
```

Create test fixture:
```bash
python manage.py dumpdata agent_app --indent 2 > fixtures/test_data.json
```

Load test fixture:
```bash
python manage.py loaddata fixtures/test_data.json
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run Django tests
        run: |
          cd agent_ui
          python manage.py test

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd tests
          npm install
      - name: Run Jest tests
        run: |
          cd tests
          npm test

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd tests
          npm install
          npx playwright install --with-deps
      - name: Run Playwright tests
        run: |
          cd tests
          npm run test:e2e
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: tests/playwright-report/
```

## Writing New Tests

### Backend Test Example

```python
from django.test import TestCase
from agent_app.models import ChatSession

class MyNewTests(TestCase):
    def setUp(self):
        self.session = ChatSession.objects.create(
            session_key='test',
            title='Test'
        )
    
    def test_something(self):
        self.assertEqual(self.session.title, 'Test')
```

### Frontend Test Example

```javascript
describe('My Feature', () => {
  test('does something', () => {
    expect(true).toBe(true);
  });
});
```

### E2E Test Example

```javascript
test('user can do something', async ({ page }) => {
  await page.goto('/');
  await page.click('#some-button');
  await page.waitForSelector('.result');
  
  const result = await page.textContent('.result');
  expect(result).toBe('Expected text');
});
```

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on other tests
2. **Clear Names**: Use descriptive test names that explain what is being tested
3. **Arrange-Act-Assert**: Structure tests with clear setup, action, and verification
4. **Mock External Services**: Don't make real API calls to external services
5. **Clean Up**: Always clean up test data to avoid side effects
6. **Fast Tests**: Keep tests fast by mocking slow operations
7. **Readable Assertions**: Use clear assertion messages

## Troubleshooting

### Django Tests Fail to Find Models
- Ensure `agent_app` is in `INSTALLED_APPS` in settings
- Run migrations: `python manage.py migrate`

### Frontend Tests Can't Find Modules
- Run `npm install` in the tests directory
- Check `package.json` for correct dependencies

### Playwright Tests Timeout
- Increase timeout in `playwright.config.js`
- Ensure dev server is running on correct port
- Check network connectivity

### Database Issues
- Use `TransactionTestCase` instead of `TestCase` for tests that need committed data
- Clear test database: `python manage.py flush --no-input`

## Test Metrics

Track these metrics to ensure quality:
- **Code Coverage**: Aim for >80% coverage
- **Test Success Rate**: Should be 100% on main branch
- **Test Execution Time**: Keep under 5 minutes for full suite
- **Flaky Test Rate**: Should be <5%

## Resources

- [Django Testing Documentation](https://docs.djangoproject.com/en/4.2/topics/testing/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Testing Best Practices](https://testingjavascript.com/)
