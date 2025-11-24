✅ Complete Integration Delivered 🔐 Admin User Setup nate@ravenhelm.co
configured as platform_owner with full platform access Script created:
scripts/setup_admin_user.py One-command initialization:
scripts/initialize_rbac.sh 🔗 NextAuth ↔ RBAC Integration Updated NextAuth
(app/api/auth/[...nextauth]/route.ts) Fetches permissions from backend during
sign-in Stores in JWT token with org_id, permissions[], roles[] Includes RBAC
data in session object Backend API (backend/main.py) New endpoint: POST
/api/auth/user-permissions Looks up user by email and returns permissions Called
automatically during NextAuth flow Session Types (types/next-auth.d.ts) Extended
to include organizationId, permissions, roles Full TypeScript support 🎨
Frontend Components usePermissions Hook (app/lib/hooks/usePermissions.ts) const
{ isPlatformAdmin, canCreateAgents, hasPermission } = usePermissions()
PermissionGate Component (app/components/auth/PermissionGate.tsx)
<PermissionGate permission="agent:create"> <CreateAgentButton />
</PermissionGate> Auth Utilities (app/lib/auth.ts) Helper functions for
permission checking Role checking (isPlatformAdmin, isOrgAdmin) 📚 Documentation
docs/RBAC_NEXTAUTH_INTEGRATION.md - Complete integration guide
RBAC_QUICKSTART.md - 5-minute getting started guide All previous RBAC docs still
apply 🚀 Next Steps (5 Minutes)

1. Run Initialization Script cd
   /Users/nwalker/Development/Projects/agentfoundry./scripts/initialize_rbac.sh
   This will: Initialize RBAC database tables Seed 60+ permissions and roles
   Create nate@ravenhelm.co as platform_owner
2. Restart Backend docker-compose restart backend
3. Sign In Go to http://localhost:3000 Sign in with nate@ravenhelm.co via Google
   OAuth You'll have full platform_owner permissions! 🎉
4. Verify in Browser Console // Check your
   permissionsconsole.log(window.next.router.query)// Or use React DevTools to
   inspect session 💡 Quick Examples Frontend: Show Button Only to Admins
   <PermissionGate permission="agent:create"> <button>Create
   Agent</button></PermissionGate> Frontend: Check Permission Before Action
   const { hasPermission } = usePermissions()if
   (hasPermission("agent:delete:org")) { deleteAgent(agentId)} Backend: Protect
   Route from backend.rbac_middleware import
   RequirePermission@app.post("/api/agents")async def create_agent( context:
   RequestContext = Depends(RequirePermission("agent:create"))): return
   create_agent_logic(context.organization_id) 📋 Your Admin Permissions As
   platform_owner, you have 20+ permissions including: ✅ Manage all
   organizations ✅ Manage all users ✅ Full agent control (create, update,
   delete) ✅ View all sessions and artifacts ✅ Access audit logs ✅ Configure
   platform settings ✅ Manage LLM quotas 📖 Documentation Guide Start here:
   RBAC_QUICKSTART.md (this summary) Integration details:
   docs/RBAC_NEXTAUTH_INTEGRATION.md Full RBAC guide:
   docs/RBAC_IMPLEMENTATION.md Quick reference: docs/RBAC_QUICK_REFERENCE.md
   Example code: backend/example_rbac_routes.py
