#!/usr/bin/env python3
"""
Diagnose Langfuse configuration and trace structure
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Langfuse Configuration Diagnostics")
print("=" * 70)
print()

# 1. Check environment
print("1. Environment Variables:")
print(f"   LANGFUSE_ENABLED: {os.getenv('LANGFUSE_ENABLED')}")
print(f"   LANGFUSE_HOST: {os.getenv('LANGFUSE_HOST')}")
print(f"   LANGFUSE_PUBLIC_KEY: {os.getenv('LANGFUSE_PUBLIC_KEY', 'Not set')[:20]}...")
print(f"   LANGFUSE_SECRET_KEY: {'Set' if os.getenv('LANGFUSE_SECRET_KEY') else 'Not set'}")
print(f"   OBSERVABILITY_DASHBOARD: {os.getenv('OBSERVABILITY_DASHBOARD')}")
print()

# 2. Check Langfuse SDK
print("2. Langfuse SDK:")
try:
    import langfuse
    print(f"   ✓ Installed")
    print(f"   Version: {langfuse.__version__ if hasattr(langfuse, '__version__') else 'Unknown'}")
    
    # Check for required classes
    from langfuse import Langfuse
    from langfuse.types import TraceContext
    print(f"   ✓ Langfuse class available")
    print(f"   ✓ TraceContext available")
    
    # Test TraceContext behavior
    test_context = TraceContext(trace_id="test123", observation_id="obs456")
    print(f"   TraceContext type: {type(test_context)}")
    print(f"   TraceContext keys: {list(test_context.keys()) if isinstance(test_context, dict) else 'N/A'}")
    
except ImportError as e:
    print(f"   ❌ Not installed: {e}")
except Exception as e:
    print(f"   ❌ Error: {e}")
print()

# 3. Test client creation
print("3. Client Creation:")
try:
    from observability import get_langfuse_client
    client = get_langfuse_client()
    if client:
        print(f"   ✓ Client created")
        print(f"   Type: {type(client).__name__}")
        print(f"   Has create_trace_id: {hasattr(client, 'create_trace_id')}")
        print(f"   Has start_observation: {hasattr(client, 'start_observation')}")
        print(f"   Has flush: {hasattr(client, 'flush')}")
    else:
        print(f"   ❌ Client is None")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
print()

# 4. Test trace creation
print("4. Test Trace Creation:")
try:
    from observability import get_langfuse_client
    from langfuse.types import TraceContext
    
    client = get_langfuse_client()
    if client:
        # Create parent
        trace_id = client.create_trace_id()
        print(f"   ✓ Trace ID created: {trace_id}")
        
        parent_context = TraceContext(trace_id=trace_id, user_id="test_user")
        print(f"   ✓ Parent context: {parent_context}")
        
        parent_obs = client.start_observation(
            trace_context=parent_context,
            name="test_parent",
            as_type="agent"
        )
        print(f"   ✓ Parent observation created")
        print(f"     ID: {parent_obs.id if hasattr(parent_obs, 'id') else 'No ID'}")
        print(f"     Type: {type(parent_obs).__name__}")
        
        # Create child
        child_context = TraceContext(
            trace_id=trace_id,
            observation_id=parent_obs.id
        )
        print(f"   ✓ Child context: {child_context}")
        print(f"     Should link to parent: {parent_obs.id}")
        
        child_obs = client.start_observation(
            trace_context=child_context,
            name="test_child",
            as_type="tool"
        )
        print(f"   ✓ Child observation created")
        print(f"     ID: {child_obs.id if hasattr(child_obs, 'id') else 'No ID'}")
        
        # End observations
        child_obs.end()
        parent_obs.end()
        client.flush()
        print(f"   ✓ Observations ended and flushed")
        print()
        print(f"   📊 Test trace created:")
        print(f"      Trace ID: {trace_id}")
        print(f"      Parent ID: {parent_obs.id}")
        print(f"      Child ID: {child_obs.id}")
        print()
        print(f"   🔍 Check in Langfuse dashboard:")
        print(f"      {os.getenv('OBSERVABILITY_DASHBOARD')}")
        print(f"      Search for: {trace_id}")
        print()
        print(f"   Expected structure:")
        print(f"      test_parent")
        print(f"      └─ test_child")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
print()

print("=" * 70)
print("✅ Diagnostics complete")
print()
print("📋 Summary:")
print("   1. Check if client creation succeeded")
print("   2. Check if test trace was created")
print("   3. Verify test trace in Langfuse dashboard")
print("   4. Confirm child appears under parent")
print()
print("If child does NOT appear under parent:")
print("   - SDK version issue")
print("   - API compatibility issue")
print("   - Langfuse dashboard caching")
