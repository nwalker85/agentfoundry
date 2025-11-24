'use client';

import { Users, UserPlus, Settings, Mail } from 'lucide-react';
import { PageHeader } from '@/app/components/shared/PageHeader';
import { UnderConstruction } from '@/components/shared';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';

// Mock data - replace with real data from API
const teamMembers = [
  {
    id: '1',
    name: 'John Doe',
    email: 'john@example.com',
    role: 'org_admin',
    avatar: null,
    status: 'active',
  },
  {
    id: '2',
    name: 'Jane Smith',
    email: 'jane@example.com',
    role: 'org_developer',
    avatar: null,
    status: 'active',
  },
];

const roleLabels: Record<string, { label: string; variant: any }> = {
  org_admin: { label: 'Admin', variant: 'default' },
  org_developer: { label: 'Developer', variant: 'secondary' },
  org_operator: { label: 'Operator', variant: 'secondary' },
  org_viewer: { label: 'Viewer', variant: 'outline' },
};

export default function TeamsPage() {
  return (
    <div className="flex-1 overflow-auto">
      <div className="container mx-auto p-6 max-w-7xl">
        <PageHeader
          title="Teams"
          description="Manage your organization's team members, roles, and permissions"
          icon={Users}
          actions={
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </Button>
              <Button size="sm">
                <UserPlus className="w-4 h-4 mr-2" />
                Invite Member
              </Button>
            </div>
          }
        />

        <UnderConstruction
          className="mt-4"
          message="Team management is under development. The data shown is placeholder only."
        />

        <div className="mt-6 grid gap-6">
          {/* Team Overview Card */}
          <Card>
            <CardHeader>
              <CardTitle>Team Overview</CardTitle>
              <CardDescription>
                {teamMembers.length} active members in your organization
              </CardDescription>
            </CardHeader>
          </Card>

          {/* Team Members List */}
          <Card>
            <CardHeader>
              <CardTitle>Team Members</CardTitle>
              <CardDescription>Manage roles and permissions for your team</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {teamMembers.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-bg-2 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <Avatar className="h-10 w-10">
                        <AvatarImage src={member.avatar || undefined} />
                        <AvatarFallback>
                          {member.name
                            .split(' ')
                            .map((n) => n[0])
                            .join('')}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className="font-medium text-fg-0">{member.name}</div>
                        <div className="text-sm text-fg-2 flex items-center gap-2">
                          <Mail className="w-3 h-3" />
                          {member.email}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant={roleLabels[member.role]?.variant || 'outline'}>
                        {roleLabels[member.role]?.label || member.role}
                      </Badge>
                      <Button variant="ghost" size="sm">
                        <Settings className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Pending Invitations */}
          <Card>
            <CardHeader>
              <CardTitle>Pending Invitations</CardTitle>
              <CardDescription>Team members who haven't accepted their invites yet</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-fg-2">No pending invitations</div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
