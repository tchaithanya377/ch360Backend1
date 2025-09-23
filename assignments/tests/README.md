# Assignments App Test Suite

This directory contains comprehensive pytest-django unit tests for the assignments app, targeting **100% code coverage**.

## Test Structure

### Core Test Files

- **`factories.py`** - Test data factories using model-bakery for all models
- **`test_models.py`** - Model tests covering creation, relationships, constraints, and custom methods
- **`test_serializers.py`** - Serializer tests covering validation, serialization, and edge cases
- **`test_views.py`** - API endpoint tests covering CRUD operations, permissions, and error handling
- **`test_permissions.py`** - Permission class tests covering all custom permission logic
- **`test_signals.py`** - Signal handler tests covering pre_save and post_save logic
- **`test_admin.py`** - Admin interface tests covering forms, configurations, and customizations

## Test Coverage

### 1. Models (`test_models.py`)
✅ **Complete Coverage**
- All model creation and validation
- String representations (`__str__` methods)
- Model relationships and foreign keys
- Unique constraints and database integrity
- Custom model methods and properties
- Model choice fields and validation
- Complex workflow scenarios

**Models Tested:**
- `AssignmentCategory`
- `Assignment`
- `AssignmentSubmission`
- `AssignmentFile`
- `AssignmentGrade`
- `AssignmentComment`
- `AssignmentGroup`
- `AssignmentTemplate`
- `AssignmentRubric`
- `AssignmentRubricGrade`
- `AssignmentPeerReview`
- `AssignmentPlagiarismCheck`
- `AssignmentLearningOutcome`
- `AssignmentAnalytics`
- `AssignmentNotification`
- `AssignmentSchedule`

### 2. Serializers (`test_serializers.py`)
✅ **Complete Coverage**
- Serialization and deserialization
- Field validation and error handling
- Custom serializer methods
- Nested serialization
- Context-dependent behavior
- Edge cases and error scenarios

**Serializers Tested:**
- `AssignmentCategorySerializer`
- `AssignmentSerializer` / `AssignmentCreateSerializer`
- `AssignmentSubmissionSerializer` / `AssignmentSubmissionCreateSerializer`
- `AssignmentFileSerializer`
- `AssignmentGradeSerializer`
- `AssignmentCommentSerializer`
- `AssignmentGroupSerializer`
- `AssignmentTemplateSerializer` / `AssignmentTemplateCreateSerializer`
- Statistics serializers
- Advanced feature serializers (rubrics, peer review, etc.)
- Simple serializers

### 3. Views / API Endpoints (`test_views.py`)
✅ **Complete Coverage**
- CRUD operations for all models
- Authentication and authorization
- Permission-based access control
- Query filtering and pagination
- Error handling (400, 401, 403, 404)
- Complex workflow scenarios

**Endpoints Tested:**
- Assignment categories CRUD
- Assignment CRUD with publishing/closing
- Submission CRUD with late detection
- Grading endpoints
- Comment system
- File upload handling
- Template management
- Statistics endpoints
- Bulk operations

### 4. Permissions (`test_permissions.py`)
✅ **Complete Coverage**
- All custom permission classes
- Role-based access (Faculty, Student, Admin, HOD)
- Object-level permissions
- Read vs. write permissions
- Edge cases and error handling

**Permissions Tested:**
- `IsFacultyOrReadOnly`
- `IsStudentOrReadOnly`
- `IsAssignmentOwnerOrReadOnly`
- `IsSubmissionOwnerOrFaculty`
- `CanGradeAssignment`
- `IsHODOrAdmin`

### 5. Signals (`test_signals.py`)
✅ **Complete Coverage**
- Pre-save and post-save signal handlers
- Signal integration with model operations
- Error handling in signals
- Performance testing
- Signal disconnection/reconnection

**Signals Tested:**
- `assignment_pre_save` - Auto-title generation, due date validation
- `submission_post_save` - Late submission detection
- `assignment_post_save` - Notification triggers

### 6. Admin (`test_admin.py`)
✅ **Complete Coverage**
- Admin model registration
- List display and filtering
- Search functionality
- Custom admin forms
- Admin methods and customizations
- Error handling in admin

**Admin Classes Tested:**
- `AssignmentCategoryAdmin`
- `AssignmentAdmin`
- `AssignmentSubmissionAdmin`
- `AssignmentGradeAdmin`
- `AssignmentAdminForm`

## Running Tests

### Prerequisites
```bash
pip install pytest pytest-django model-bakery
```

### Run All Tests
```bash
# Run all assignment tests
pytest assignments/tests/

# Run with coverage
pytest assignments/tests/ --cov=assignments --cov-report=html

# Run specific test file
pytest assignments/tests/test_models.py

# Run specific test class
pytest assignments/tests/test_models.py::TestAssignmentModel

# Run specific test method
pytest assignments/tests/test_models.py::TestAssignmentModel::test_assignment_creation
```

### Test Configuration
Tests are configured to use:
- **pytest-django** for Django integration
- **model-bakery** for test data generation
- **APIClient** for API testing
- **Mock** objects for external dependencies

## Test Data Management

### Factories (`factories.py`)
Comprehensive factories for all models using model-bakery:

```python
# Basic usage
assignment = assignment_factory.make()
submission = assignment_submission_factory.make(assignment=assignment)

# Specialized factories
published_assignment = published_assignment_factory()
late_submission = late_submission_factory()
graded_submission = graded_submission_factory()

# Complex workflows
workflow = complete_assignment_workflow_factory()
```

### Factory Features
- **Relationship handling** - Automatic foreign key creation
- **Realistic data** - Meaningful test data generation
- **Edge case factories** - Specialized scenarios
- **Workflow factories** - Complete business processes
- **Bulk data creation** - Performance testing support

## Test Categories

### Happy Path Tests
- Normal CRUD operations
- Valid data processing
- Expected user workflows
- Successful integrations

### Error Path Tests
- Invalid data handling
- Permission violations
- Missing required fields
- Constraint violations
- Network/database errors

### Edge Case Tests
- Boundary conditions
- Null/empty values
- Large data sets
- Concurrent operations
- Timezone handling

### Integration Tests
- Multi-model workflows
- Signal interactions
- Permission combinations
- End-to-end scenarios

## Performance Considerations

### Database Optimization
- Uses `pytest.mark.django_db` for database access
- Minimal database queries in test setup
- Bulk operations where appropriate
- Transaction rollback for isolation

### Test Isolation
- Each test is independent
- Database state reset between tests
- Mock external dependencies
- Parallel execution safe

## Coverage Goals

Target: **100% Code Coverage**

### Current Coverage Areas
- ✅ Model logic and validation
- ✅ Serializer validation and methods
- ✅ View logic and permissions
- ✅ Custom permission classes
- ✅ Signal handlers
- ✅ Admin configurations
- ✅ Error handling
- ✅ Edge cases

### Coverage Verification
```bash
# Generate coverage report
pytest assignments/tests/ --cov=assignments --cov-report=html --cov-report=term

# View detailed coverage
open htmlcov/index.html
```

## Best Practices Implemented

### Test Organization
- Clear test class hierarchy
- Descriptive test method names
- Logical grouping of related tests
- Comprehensive docstrings

### Data Management
- Factory-based test data
- Minimal data setup
- Realistic test scenarios
- Edge case coverage

### Assertion Strategy
- Specific assertions
- Multiple assertion types
- Error message validation
- State verification

### Performance
- Fast test execution
- Minimal database usage
- Efficient queries
- Parallel-safe design

## Maintenance

### Adding New Tests
1. Follow existing naming conventions
2. Use appropriate factories for test data
3. Include both happy and error paths
4. Add docstrings explaining test purpose
5. Ensure test isolation

### Updating Tests
1. Update when models/views change
2. Maintain factory definitions
3. Keep coverage at 100%
4. Update documentation

### Debugging Tests
```bash
# Run with verbose output
pytest assignments/tests/ -v

# Run with pdb debugging
pytest assignments/tests/ --pdb

# Run specific failing test
pytest assignments/tests/test_models.py::TestAssignmentModel::test_specific_case -v
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run Assignment Tests
  run: |
    pytest assignments/tests/ --cov=assignments --cov-fail-under=100
```

### Pre-commit Hooks
```yaml
- repo: local
  hooks:
    - id: pytest-assignments
      name: pytest-assignments
      entry: pytest assignments/tests/
      language: system
      pass_filenames: false
```

## Contributing

When adding new features to the assignments app:

1. **Write tests first** (TDD approach)
2. **Update factories** if new models are added
3. **Maintain 100% coverage**
4. **Test all user roles** (Faculty, Student, Admin)
5. **Include error scenarios**
6. **Document complex test cases**

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed
   - Check PYTHONPATH includes project root

2. **Database Issues**
   - Use `pytest.mark.django_db` decorator
   - Check database configuration in settings

3. **Permission Errors**
   - Verify user setup in test fixtures
   - Check authentication in API tests

4. **Factory Issues**
   - Update factory definitions when models change
   - Check foreign key relationships

### Getting Help

- Check existing test patterns in the codebase
- Review Django and DRF testing documentation
- Consult pytest-django documentation
- Review model-bakery usage examples
