# Component Patterns Analysis

## Architecture Overview

### State Management Approach
**Pattern:** React Context + Local State
- **AuthContext:** Global authentication state (user, token, login/logout)
- **Component State:** Local useState for UI state, data fetching, modals
- **No Redux/Zustand:** Simple context-based approach

### Data Fetching Pattern
**Pattern:** useEffect + fetch API
```typescript
useEffect(() => {
  const fetchData = async () => {
    try {
      const res = await fetch(`${API_URL}/endpoint`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setData(data)
      }
    } catch (err) {
      // Handle error
    }
  }
  fetchData()
}, [dependencies])
```

**Characteristics:**
- No custom hooks for data fetching
- No caching layer
- No request deduplication
- Manual loading/error state management
- Direct fetch calls (no axios/react-query)

## Component Composition Patterns

### 1. Page Components (Container Pattern)

**Example:** `Results.tsx`, `Dashboard.tsx`, `Assessment.tsx`

**Structure:**
```
Page Component
├── Data Fetching (useEffect)
├── State Management (useState)
├── Business Logic
├── Conditional Rendering
└── Child Components
```

**Characteristics:**
- Self-contained data fetching
- Inline styles object at bottom
- Multiple responsibilities (data + UI + logic)
- No separation of concerns

**Props Pattern:**
```typescript
interface ResultsProps {
  assessmentId: string
  mode: string
}
```
- Simple, typed props
- No children prop pattern
- No render props
- No compound components

### 2. Modal Components (Portal Pattern)

**Example:** `PaywallModal.tsx`, `UpgradeModal.tsx`

**Structure:**
```typescript
interface ModalProps {
  isOpen: boolean
  onClose: () => void
  // Additional action handlers
}

export default function Modal({ isOpen, onClose }: ModalProps) {
  if (!isOpen) return null
  
  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        {/* Content */}
      </div>
    </div>
  )
}
```

**Characteristics:**
- Controlled visibility (isOpen prop)
- Callback props for actions (onClose, onUpgrade)
- Overlay click-to-close
- Event propagation stopping
- No React Portal usage (renders in place)
- No focus management
- No body scroll lock

### 3. Display Components (Presentational Pattern)

**Example:** `UsageBadge.tsx`

**Structure:**
```typescript
export default function UsageBadge() {
  const { user, token } = useAuth()
  const [data, setData] = useState(null)
  
  useEffect(() => {
    // Fetch data
  }, [user, token])
  
  if (!data || condition) return null
  
  return <div>{/* Display */}</div>
}
```

**Characteristics:**
- Self-fetching (not purely presentational)
- Conditional rendering (return null)
- No props (uses context directly)
- Silent failures

## Props Patterns

### 1. Callback Props
```typescript
interface ModalProps {
  onClose: () => void
  onUpgrade: () => void
}
```
- Simple void functions
- No event objects passed
- No data passed back to parent

### 2. Data Props
```typescript
interface ResultsProps {
  assessmentId: string
  mode: string
}
```
- Primitive types preferred
- No complex object props
- IDs passed instead of full objects

### 3. Conditional Props
```typescript
interface UpgradeModalProps {
  isOpen: boolean
  onClose: () => void
}
```
- Boolean flags for visibility
- No optional chaining in props
- Required props (no defaults)

## Styling Patterns

### 1. Inline Styles Object Pattern
```typescript
const styles = {
  container: {
    minHeight: '100vh',
    background: '#000000',
    color: '#c0ffc0',
  },
  button: {
    padding: '12px 24px',
    cursor: 'pointer',
  }
}

// Usage
<div style={styles.container}>
```

**Characteristics:**
- All styles defined at component bottom
- No CSS modules
- No styled-components
- No Tailwind CSS
- Type casting for specific values: `as const`

### 2. Dynamic Style Composition
```typescript
<button
  style={{
    ...styles.planOption,
    ...(active ? styles.planOptionActive : {}),
  }}
>
```

**Pattern:**
- Spread base styles
- Conditionally spread modifier styles
- No className manipulation
- No CSS-in-JS libraries

### 3. Inline Dynamic Styles
```typescript
<div
  style={{
    ...styles.levelBadge,
    color: levelColor,
    border: `2px solid ${levelColor}`,
    background: `${levelColor}15`,
  }}
>
```

**Pattern:**
- Merge static and dynamic styles
- Template literals for computed values
- Hex color with alpha (e.g., `${color}15`)

### 4. Style Constants
```typescript
const PRIMARY_GRADIENT = 'linear-gradient(135deg, #6D5FFA 0%, #8B5CF6 50%, #EC41FB 100%)'

// Usage
background: PRIMARY_GRADIENT
```

**Pattern:**
- Module-level constants for reused values
- No centralized theme file
- Duplicated across components

## State Management Patterns

### 1. Local State Pattern
```typescript
const [data, setData] = useState<DataType | null>(null)
const [loading, setLoading] = useState(true)
const [error, setError] = useState<string | null>(null)
```

**Characteristics:**
- Separate state variables for data/loading/error
- Nullable types (Type | null)
- Boolean flags for UI state
- No state machines

### 2. Modal State Pattern
```typescript
const [showModal, setShowModal] = useState(false)

// Open
setShowModal(true)

// Close
setShowModal(false)
```

**Characteristics:**
- Boolean state for visibility
- Direct state updates
- No modal manager/context
- Multiple modal states in same component

### 3. Form State Pattern
```typescript
const [plan, setPlan] = useState<BillingPlan>('premium_monthly')
const [loading, setLoading] = useState(false)
const [error, setError] = useState('')
```

**Characteristics:**
- Controlled inputs
- No form libraries (no react-hook-form)
- Manual validation
- String error messages

### 4. Animation State Pattern
```typescript
const [scoreAnimated, setScoreAnimated] = useState(0)

useEffect(() => {
  const target = Math.round(data.final_score)
  let current = 0
  const step = Math.max(1, Math.floor(target / 40))
  const interval = setInterval(() => {
    current += step
    if (current >= target) {
      current = target
      clearInterval(interval)
    }
    setScoreAnimated(current)
  }, 30)
  return () => clearInterval(interval)
}, [data])
```

**Pattern:**
- setInterval for animations
- Cleanup in useEffect return
- State-driven animation values

## Context Usage Pattern

### AuthContext Implementation
```typescript
// Provider
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  
  // localStorage sync
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token')
    const storedUser = localStorage.getItem('auth_user')
    if (storedToken && storedUser) {
      setToken(storedToken)
      setUser(JSON.parse(storedUser))
    }
  }, [])
  
  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  )
}

// Consumer Hook
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
```

**Characteristics:**
- Single context for auth
- localStorage persistence
- Custom hook with error checking
- No context splitting
- No memoization of context value

## API Integration Patterns

### 1. Environment Variable Pattern
```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
```

**Characteristics:**
- Vite environment variables
- Fallback to localhost
- No API client abstraction
- Repeated in every component

### 2. Authorization Header Pattern
```typescript
const res = await fetch(`${API_URL}/endpoint`, {
  headers: { Authorization: `Bearer ${token}` }
})
```

**Characteristics:**
- Manual header construction
- Token from context
- No interceptors
- No automatic retry

### 3. Response Handling Pattern
```typescript
const res = await fetch(url)
if (!res.ok) {
  const data = await res.json()
  throw new Error(data.detail || 'Failed')
}
const data = await res.json()
```

**Characteristics:**
- Manual ok check
- Error detail extraction
- No response type validation
- No error normalization

### 4. Error Handling Pattern
```typescript
try {
  // API call
} catch (err) {
  setError(err instanceof Error ? err.message : 'Unknown error')
}
```

**Characteristics:**
- Type guard for Error
- Fallback error message
- No error reporting service
- No retry logic

## Conditional Rendering Patterns

### 1. Early Return Pattern
```typescript
if (!isOpen) return null
if (loading) return <LoadingSpinner />
if (error) return <ErrorMessage />
return <MainContent />
```

**Characteristics:**
- Guard clauses at top
- Reduces nesting
- Clear state hierarchy

### 2. Ternary Pattern
```typescript
{isAuthenticated ? (
  <AuthenticatedView />
) : (
  <UnauthenticatedView />
)}
```

**Characteristics:**
- Inline ternaries
- JSX in both branches
- No intermediate variables

### 3. Logical AND Pattern
```typescript
{data.usage.tier === 'premium' && (
  <PremiumFeature />
)}

{error && <div style={styles.error}>{error}</div>}
```

**Characteristics:**
- Short-circuit evaluation
- No explicit true check
- Falsy values handled implicitly

### 4. Nullish Coalescing Pattern
```typescript
{results.psv_score !== null && (
  <div>{Math.round(results.psv_score)}</div>
)}
```

**Characteristics:**
- Explicit null checks
- No optional chaining in JSX
- Strict equality checks

## Event Handling Patterns

### 1. Inline Arrow Functions
```typescript
<button onClick={() => setShowModal(true)}>
<button onClick={() => navigate('/dashboard')}>
```

**Characteristics:**
- Arrow functions in JSX
- No useCallback optimization
- Direct state updates
- Navigation calls

### 2. Event Propagation Control
```typescript
<div style={styles.overlay} onClick={onClose}>
  <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
```

**Characteristics:**
- stopPropagation for nested clicks
- Overlay click-to-close
- No event delegation

### 3. Async Event Handlers
```typescript
const handleUpgrade = async () => {
  setLoading(true)
  setError('')
  try {
    const response = await fetch(...)
    // Handle response
  } catch {
    setError('...')
  } finally {
    setLoading(false)
  }
}
```

**Characteristics:**
- Async/await syntax
- Loading state management
- Error state clearing
- Finally block for cleanup

## Data Flow Patterns

### 1. Props Down, Events Up
```
Parent Component
    ├── State: showModal
    ├── Handler: setShowModal
    └── Pass to Child
            ↓
Child Modal
    ├── Receive: isOpen, onClose
    └── Call: onClose() on user action
            ↓
Parent receives event
    └── Updates state
```

**Characteristics:**
- Unidirectional data flow
- No prop drilling (context for auth)
- Callback props for actions

### 2. Fetch-on-Mount Pattern
```typescript
useEffect(() => {
  fetchData()
}, [])
```

**Characteristics:**
- Empty dependency array
- Runs once on mount
- No cleanup for fetch
- No abort controller

### 3. Derived State Pattern
```typescript
const isAuthenticated = !!token
const levelColor = LEVEL_COLORS[results.level] || '#00ff41'
```

**Characteristics:**
- Computed during render
- No useMemo
- Simple transformations
- Fallback values

## Type Safety Patterns

### 1. Interface Definitions
```typescript
interface User {
  id: string
  email: string
  name: string
  avatar_url?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (token: string, user: User) => void
  logout: () => void
  isAuthenticated: boolean
}
```

**Characteristics:**
- Explicit interfaces
- Optional properties with ?
- Nullable types with | null
- Function signatures in interfaces

### 2. Type Assertions
```typescript
const stateData = location.state as AssessmentData | null
```

**Characteristics:**
- Type assertions for external data
- Union with null for safety
- No runtime validation

### 3. Const Assertions
```typescript
textTransform: 'uppercase' as const
flexDirection: 'column' as const
```

**Characteristics:**
- Required for style objects
- Literal type preservation
- TypeScript strict mode compliance

### 4. Generic Types
```typescript
const [data, setData] = useState<DataType | null>(null)
```

**Characteristics:**
- Explicit type parameters
- Nullable initial state
- No type inference reliance

## Reusability Assessment

### High Reusability
- **AuthContext:** Used across multiple components
- **Modal overlay pattern:** Consistent across modals
- **Inline styles pattern:** Consistent approach

### Low Reusability
- **API fetching logic:** Duplicated in every component
- **Loading states:** Repeated pattern, no shared component
- **Error handling:** Similar code in multiple places
- **Style constants:** Duplicated colors/gradients

### Missing Abstractions
- No shared Button component
- No shared Input component
- No shared Card/Container component
- No shared Modal wrapper
- No shared Loading component
- No shared Error component
- No custom hooks for common patterns

## Performance Considerations

### Potential Issues
1. **No memoization:** Context value not memoized
2. **Inline functions:** Arrow functions in JSX (re-created on render)
3. **No code splitting:** All components loaded upfront
4. **No lazy loading:** Modals loaded even when closed
5. **Repeated API calls:** No caching or deduplication

### Current Optimizations
1. **Conditional rendering:** Early returns prevent unnecessary renders
2. **Cleanup functions:** setInterval cleanup in useEffect
3. **Minimal re-renders:** Local state prevents cascading updates

## Testing Considerations

### Testability Issues
1. **Inline styles:** Hard to test style logic
2. **Direct fetch calls:** Need to mock global fetch
3. **localStorage usage:** Need to mock localStorage
4. **No dependency injection:** Hard to swap implementations
5. **Tight coupling:** Components fetch their own data

### Testable Aspects
1. **Pure functions:** Style composition logic
2. **Type definitions:** Can validate with TypeScript
3. **Conditional rendering:** Can test with different props
4. **Event handlers:** Can test callback invocation

## Recommendations

### 1. Extract Custom Hooks
```typescript
// useApi.ts
function useApi<T>(url: string) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // ... fetch logic
  return { data, loading, error, refetch }
}

// Usage
const { data, loading, error } = useApi<UsageData>('/usage/check')
```

### 2. Create Shared Components
```typescript
// Button.tsx
interface ButtonProps {
  variant: 'primary' | 'secondary'
  onClick: () => void
  children: ReactNode
}

// Modal.tsx
interface ModalProps {
  isOpen: boolean
  onClose: () => void
  children: ReactNode
}
```

### 3. Centralize Styles
```typescript
// theme.ts
export const colors = {
  matrix: {
    primary: '#00ff41',
    secondary: '#008f11',
    background: '#000000',
  },
  premium: {
    gradient: 'linear-gradient(...)',
    text: '#F8FAFC',
  }
}

export const spacing = {
  xs: '0.25rem',
  sm: '0.5rem',
  md: '1rem',
  // ...
}
```

### 4. Create API Client
```typescript
// api.ts
class ApiClient {
  constructor(private baseUrl: string, private getToken: () => string | null) {}
  
  async get<T>(endpoint: string): Promise<T> {
    const token = this.getToken()
    const res = await fetch(`${this.baseUrl}${endpoint}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
    if (!res.ok) throw new Error(await this.extractError(res))
    return res.json()
  }
  
  // ... post, put, delete methods
}
```

### 5. Implement Error Boundaries
```typescript
class ErrorBoundary extends React.Component {
  state = { hasError: false }
  
  static getDerivedStateFromError() {
    return { hasError: true }
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallback />
    }
    return this.props.children
  }
}
```

### 6. Add Loading Skeletons
```typescript
// LoadingSkeleton.tsx
export function CardSkeleton() {
  return (
    <div style={styles.skeleton}>
      <div style={styles.shimmer} />
    </div>
  )
}
```

### 7. Optimize Context
```typescript
const value = useMemo(
  () => ({ user, token, login, logout, isAuthenticated }),
  [user, token]
)
```

### 8. Add Request Cancellation
```typescript
useEffect(() => {
  const controller = new AbortController()
  
  fetch(url, { signal: controller.signal })
    .then(...)
    .catch(err => {
      if (err.name !== 'AbortError') {
        setError(err.message)
      }
    })
  
  return () => controller.abort()
}, [url])
```
