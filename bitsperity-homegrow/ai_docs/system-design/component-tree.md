# HomeGrow v3 - Component Tree

## Frontend Architektur Übersicht

HomeGrow v3 verwendet **SvelteKit** mit einer **hierarchischen Component-Struktur** und **Svelte Stores** für State Management. Die Architektur folgt dem **Atomic Design Pattern** mit einer klaren Trennung zwischen UI-, Feature- und Layout-Komponenten.

```
Frontend Architecture:
├── Routes (Pages)           # SvelteKit page components
├── Layouts                  # Shared layouts and navigation  
├── Feature Components       # Domain-specific business logic
├── UI Components            # Reusable atomic components
├── Stores                   # State management
└── Utils                    # Helper functions
```

## Root Layout Structure

```
src/
├── app.html                 # Root HTML template
├── routes/
│   ├── +layout.svelte      # Root layout (navigation, theme)
│   ├── +layout.js          # Layout load function
│   ├── +page.svelte        # Dashboard home page
│   └── ... (page routes)
```

### Root Layout (+layout.svelte)
```svelte
<!-- src/routes/+layout.svelte -->
<script lang="ts">
  import Navigation from '$lib/components/layout/Navigation.svelte';
  import ThemeProvider from '$lib/components/layout/ThemeProvider.svelte';
  import NotificationContainer from '$lib/components/alerts/NotificationContainer.svelte';
  import LoadingOverlay from '$lib/components/ui/LoadingOverlay.svelte';
  import ErrorBoundary from '$lib/components/layout/ErrorBoundary.svelte';
  
  import { websocketStore } from '$lib/stores/websocket.js';
  import { themeStore } from '$lib/stores/theme.js';
  import { notificationStore } from '$lib/stores/notifications.js';
  import { onMount } from 'svelte';
  
  onMount(() => {
    // Initialize WebSocket connection
    websocketStore.connect();
  });
</script>

<ThemeProvider theme={$themeStore}>
  <div class="app-container">
    <Navigation />
    
    <main class="main-content">
      <ErrorBoundary>
        <slot />
      </ErrorBoundary>
    </main>
    
    <NotificationContainer notifications={$notificationStore} />
    <LoadingOverlay />
  </div>
</ThemeProvider>
```

## Page Components (Routes)

### 1. Dashboard (src/routes/+page.svelte)
```svelte
<script lang="ts">
  import StatusCards from '$lib/components/dashboard/StatusCards.svelte';
  import DeviceGrid from '$lib/components/dashboard/DeviceGrid.svelte';
  import QuickActions from '$lib/components/dashboard/QuickActions.svelte';
  import RecentActivity from '$lib/components/dashboard/RecentActivity.svelte';
  import SystemHealth from '$lib/components/dashboard/SystemHealth.svelte';
  
  import { devicesStore } from '$lib/stores/devices.js';
  import { programsStore } from '$lib/stores/programs.js';
  import { alertsStore } from '$lib/stores/alerts.js';
</script>

<div class="dashboard">
  <header class="dashboard-header">
    <h1>HomeGrow Dashboard</h1>
    <SystemHealth />
  </header>
  
  <StatusCards 
    devices={$devicesStore.devices}
    programs={$programsStore.instances}
    alerts={$alertsStore.active}
  />
  
  <div class="dashboard-grid">
    <section class="devices-section">
      <DeviceGrid devices={$devicesStore.devices} />
    </section>
    
    <aside class="sidebar">
      <QuickActions />
      <RecentActivity activities={$devicesStore.recentActivity} />
    </aside>
  </div>
</div>
```

### 2. Device Management (src/routes/devices/+page.svelte)
```svelte
<script lang="ts">
  import DeviceDiscovery from '$lib/components/devices/DeviceDiscovery.svelte';
  import DeviceList from '$lib/components/devices/DeviceList.svelte';
  import DeviceFilters from '$lib/components/devices/DeviceFilters.svelte';
  import AddDeviceModal from '$lib/components/devices/AddDeviceModal.svelte';
  
  import { devicesStore } from '$lib/stores/devices.js';
  
  let showAddModal = false;
  let filters = { status: 'all', location: 'all' };
</script>

<div class="devices-page">
  <header class="page-header">
    <h1>Device Management</h1>
    <button on:click={() => showAddModal = true}>Add Device</button>
  </header>
  
  <DeviceDiscovery />
  
  <div class="devices-content">
    <DeviceFilters bind:filters />
    <DeviceList devices={$devicesStore.filteredDevices} {filters} />
  </div>
  
  {#if showAddModal}
    <AddDeviceModal bind:show={showAddModal} />
  {/if}
</div>
```

### 3. Monitoring (src/routes/monitoring/+page.svelte)
```svelte
<script lang="ts">
  import SensorCharts from '$lib/components/monitoring/SensorCharts.svelte';
  import LiveReadings from '$lib/components/monitoring/LiveReadings.svelte';
  import ChartControls from '$lib/components/monitoring/ChartControls.svelte';
  import DataExport from '$lib/components/monitoring/DataExport.svelte';
  
  import { sensorsStore } from '$lib/stores/sensors.js';
  import { devicesStore } from '$lib/stores/devices.js';
  
  let selectedDevices = [];
  let timeRange = '24h';
  let sensorTypes = ['ph', 'tds'];
</script>

<div class="monitoring-page">
  <header class="page-header">
    <h1>Real-time Monitoring</h1>
    <DataExport {selectedDevices} {timeRange} />
  </header>
  
  <LiveReadings 
    devices={$devicesStore.devices}
    sensorData={$sensorsStore.current}
  />
  
  <ChartControls 
    bind:selectedDevices
    bind:timeRange
    bind:sensorTypes
    availableDevices={$devicesStore.devices}
  />
  
  <SensorCharts 
    data={$sensorsStore.historical}
    {selectedDevices}
    {timeRange}
    {sensorTypes}
  />
</div>
```

### 4. Program Management (src/routes/programs/+page.svelte)
```svelte
<script lang="ts">
  import ProgramTemplates from '$lib/components/programs/ProgramTemplates.svelte';
  import ActivePrograms from '$lib/components/programs/ActivePrograms.svelte';
  import ProgramCreator from '$lib/components/programs/ProgramCreator.svelte';
  
  import { programsStore } from '$lib/stores/programs.js';
  
  let view = 'active'; // 'active' | 'templates' | 'create'
</script>

<div class="programs-page">
  <header class="page-header">
    <h1>Growth Programs</h1>
    <nav class="tab-navigation">
      <button class:active={view === 'active'} on:click={() => view = 'active'}>
        Active Programs
      </button>
      <button class:active={view === 'templates'} on:click={() => view = 'templates'}>
        Templates
      </button>
      <button class:active={view === 'create'} on:click={() => view = 'create'}>
        Create New
      </button>
    </nav>
  </header>
  
  {#if view === 'active'}
    <ActivePrograms instances={$programsStore.instances} />
  {:else if view === 'templates'}
    <ProgramTemplates templates={$programsStore.templates} />
  {:else if view === 'create'}
    <ProgramCreator />
  {/if}
</div>
```

### 5. Manual Control (src/routes/manual/+page.svelte)
```svelte
<script lang="ts">
  import PumpControls from '$lib/components/manual/PumpControls.svelte';
  import EmergencyControls from '$lib/components/manual/EmergencyControls.svelte';
  import DeviceSelector from '$lib/components/manual/DeviceSelector.svelte';
  import CommandHistory from '$lib/components/manual/CommandHistory.svelte';
  import SafetyLimits from '$lib/components/manual/SafetyLimits.svelte';
  
  import { devicesStore } from '$lib/stores/devices.js';
  import { commandsStore } from '$lib/stores/commands.js';
  
  let selectedDevice = null;
</script>

<div class="manual-page">
  <header class="page-header">
    <h1>Manual Control</h1>
    <EmergencyControls />
  </header>
  
  <div class="manual-grid">
    <section class="device-selection">
      <DeviceSelector 
        devices={$devicesStore.devices}
        bind:selectedDevice
      />
      <SafetyLimits device={selectedDevice} />
    </section>
    
    <section class="pump-controls">
      <PumpControls 
        device={selectedDevice}
        onCommand={(cmd) => commandsStore.send(cmd)}
      />
    </section>
    
    <section class="command-history">
      <CommandHistory commands={$commandsStore.recent} />
    </section>
  </div>
</div>
```

## Feature Components

### Dashboard Components
```
src/lib/components/dashboard/
├── StatusCards.svelte           # System status overview
├── DeviceGrid.svelte           # Device status grid
├── QuickActions.svelte         # Common action buttons
├── RecentActivity.svelte       # Activity feed
├── SystemHealth.svelte         # System health indicator
└── DashboardRefresh.svelte     # Manual refresh controls
```

### Device Management Components
```
src/lib/components/devices/
├── DeviceDiscovery.svelte      # Auto-discovery interface
├── DeviceList.svelte           # Device list with filters
├── DeviceCard.svelte           # Individual device card
├── DeviceFilters.svelte        # Filtering controls
├── AddDeviceModal.svelte       # Add device dialog
├── DeviceConfig.svelte         # Device configuration
├── DeviceStatus.svelte         # Status indicator
└── DeviceActions.svelte        # Device action menu
```

### Monitoring Components
```
src/lib/components/monitoring/
├── SensorCharts.svelte         # Multi-device charts
├── LiveReadings.svelte         # Real-time sensor display
├── ChartControls.svelte        # Chart configuration
├── DataExport.svelte           # Export functionality
├── SensorCard.svelte           # Individual sensor display
├── ChartLegend.svelte          # Chart legend component
└── TimeRangeSelector.svelte    # Time range picker
```

### Program Management Components
```
src/lib/components/programs/
├── ProgramTemplates.svelte     # Template browser
├── ActivePrograms.svelte       # Running program list
├── ProgramCreator.svelte       # Template editor
├── ProgramCard.svelte          # Program display card
├── PhaseEditor.svelte          # Phase configuration
├── ProgramProgress.svelte      # Progress indicator
├── TemplateLibrary.svelte      # Public template browser
└── ProgramActions.svelte       # Program control buttons
```

### Manual Control Components
```
src/lib/components/manual/
├── PumpControls.svelte         # Pump control interface
├── EmergencyControls.svelte    # Emergency stop
├── DeviceSelector.svelte       # Device selection
├── CommandHistory.svelte       # Command log
├── SafetyLimits.svelte         # Safety configuration
├── PumpCard.svelte             # Individual pump control
└── DurationSlider.svelte       # Time duration input
```

## UI Components (Atomic Design)

### Atoms (Basic Building Blocks)
```
src/lib/components/ui/atoms/
├── Button.svelte               # Primary button component
├── Input.svelte                # Text input field
├── Select.svelte               # Dropdown select
├── Checkbox.svelte             # Checkbox input
├── RadioButton.svelte          # Radio button
├── Slider.svelte               # Range slider
├── Toggle.svelte               # Toggle switch
├── Badge.svelte                # Status badge
├── Icon.svelte                 # Icon component
├── Spinner.svelte              # Loading spinner
├── Avatar.svelte               # User/device avatar
└── Tooltip.svelte              # Tooltip overlay
```

### Molecules (Combined Atoms)
```
src/lib/components/ui/molecules/
├── Card.svelte                 # Content card
├── Modal.svelte                # Modal dialog
├── Dropdown.svelte             # Dropdown menu
├── Pagination.svelte           # Page navigation
├── Breadcrumb.svelte           # Navigation breadcrumb
├── SearchBox.svelte            # Search input with icon
├── StatusIndicator.svelte      # Status with color/text
├── ProgressBar.svelte          # Progress indicator
├── TabGroup.svelte             # Tab navigation
├── ButtonGroup.svelte          # Grouped buttons
├── FormField.svelte            # Label + input + validation
└── Toast.svelte                # Toast notification
```

### Organisms (Complex Components)
```
src/lib/components/ui/organisms/
├── DataTable.svelte            # Sortable data table
├── Chart.svelte                # Chart.js wrapper
├── Form.svelte                 # Form with validation
├── Sidebar.svelte              # Collapsible sidebar
├── Header.svelte               # Page header
├── Navigation.svelte           # Main navigation
├── FilterPanel.svelte          # Advanced filtering
├── FileUpload.svelte           # File upload interface
├── Calendar.svelte             # Date/time picker
└── ErrorBoundary.svelte        # Error handling wrapper
```

## Specialized Components

### Chart Components
```
src/lib/components/charts/
├── LineChart.svelte            # Time series line chart
├── BarChart.svelte             # Bar chart component
├── PieChart.svelte             # Pie/donut chart
├── GaugeChart.svelte           # Gauge/meter display
├── Heatmap.svelte              # Heatmap visualization
└── ChartBase.svelte            # Base chart wrapper
```

### Alert Components
```
src/lib/components/alerts/
├── NotificationContainer.svelte # Global notification area
├── AlertCard.svelte            # Individual alert display
├── AlertBadge.svelte           # Alert count badge
├── AlertFilters.svelte         # Alert filtering
└── AlertHistory.svelte         # Alert history list
```

### Layout Components
```
src/lib/components/layout/
├── Navigation.svelte           # Main app navigation
├── ThemeProvider.svelte        # Theme context provider
├── ErrorBoundary.svelte        # Error handling wrapper
├── LoadingOverlay.svelte       # Global loading state
├── PageHeader.svelte           # Standard page header
├── ContentContainer.svelte     # Main content wrapper
└── ResponsiveGrid.svelte       # Responsive grid layout
```

## Component Props & Events

### Standard Component Interface
```typescript
// Base component props
interface BaseProps {
  id?: string;
  class?: string;
  style?: string;
  disabled?: boolean;
  loading?: boolean;
}

// Event handlers
interface ComponentEvents {
  click?: (event: MouseEvent) => void;
  change?: (value: any) => void;
  input?: (value: any) => void;
  focus?: (event: FocusEvent) => void;
  blur?: (event: FocusEvent) => void;
}
```

### Domain-Specific Interfaces
```typescript
// Device-related components
interface DeviceProps {
  device: Device;
  status?: 'online' | 'offline' | 'error';
  showActions?: boolean;
  compact?: boolean;
}

// Sensor components
interface SensorProps {
  sensorData: SensorData[];
  deviceId?: string;
  sensorType?: string;
  timeRange?: string;
  showExport?: boolean;
}

// Program components
interface ProgramProps {
  program: ProgramInstance | ProgramTemplate;
  editable?: boolean;
  showProgress?: boolean;
  showActions?: boolean;
}
```

## State Management Integration

### Component-Store Connection
```svelte
<!-- Example: DeviceCard.svelte -->
<script lang="ts">
  import { devicesStore } from '$lib/stores/devices.js';
  import { commandsStore } from '$lib/stores/commands.js';
  
  export let device: Device;
  
  // Reactive statements for computed values
  $: isOnline = device.status === 'online';
  $: lastSeen = device.last_seen ? new Date(device.last_seen) : null;
  
  // Event handlers
  async function handleCommand(action: string, params: any) {
    await commandsStore.send({
      device_id: device.device_id,
      action,
      params
    });
  }
  
  function handleEdit() {
    devicesStore.setEditMode(device.device_id, true);
  }
</script>

<div class="device-card" class:online={isOnline} class:offline={!isOnline}>
  <header class="device-header">
    <h3>{device.name}</h3>
    <StatusIndicator status={device.status} />
  </header>
  
  <div class="device-content">
    <!-- Device content -->
  </div>
  
  <footer class="device-actions">
    <Button on:click={handleEdit}>Configure</Button>
    <Button on:click={() => handleCommand('test_connection', {})}>Test</Button>
  </footer>
</div>
```

## Responsive Design Strategy

### Breakpoint System
```css
/* Tailwind CSS breakpoints */
:root {
  --mobile: 640px;    /* sm */
  --tablet: 768px;    /* md */
  --desktop: 1024px;  /* lg */
  --wide: 1280px;     /* xl */
}
```

### Component Responsiveness
```svelte
<!-- Responsive component example -->
<script>
  import { onMount } from 'svelte';
  
  let screenSize = 'desktop';
  
  onMount(() => {
    function updateScreenSize() {
      if (window.innerWidth < 640) screenSize = 'mobile';
      else if (window.innerWidth < 1024) screenSize = 'tablet';
      else screenSize = 'desktop';
    }
    
    updateScreenSize();
    window.addEventListener('resize', updateScreenSize);
    
    return () => window.removeEventListener('resize', updateScreenSize);
  });
</script>

<div class="component" class:mobile={screenSize === 'mobile'}>
  {#if screenSize === 'mobile'}
    <!-- Mobile layout -->
  {:else}
    <!-- Desktop layout -->
  {/if}
</div>
```

## Performance Optimizations

### Component Lazy Loading
```typescript
// Dynamic component imports
export const LazyChart = () => import('$lib/components/charts/LineChart.svelte');
export const LazyModal = () => import('$lib/components/ui/Modal.svelte');
```

### Virtual Scrolling for Large Lists
```svelte
<!-- VirtualList.svelte for large device/sensor lists -->
<script lang="ts">
  export let items: any[];
  export let itemHeight: number = 60;
  export let containerHeight: number = 400;
  
  let scrollTop = 0;
  let visibleStart = 0;
  let visibleEnd = 0;
  
  $: {
    visibleStart = Math.floor(scrollTop / itemHeight);
    visibleEnd = Math.min(
      visibleStart + Math.ceil(containerHeight / itemHeight) + 1,
      items.length
    );
  }
</script>

<div class="virtual-list" style="height: {containerHeight}px;">
  <!-- Virtual scrolling implementation -->
</div>
```

Diese Component-Tree-Architektur bietet eine saubere, skalierbare Struktur für HomeGrow v3 mit klarer Trennung der Verantwortlichkeiten und optimaler Wiederverwendbarkeit. 