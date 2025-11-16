"use client"

import { useState, useRef, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { Camera, Save, User, Palette } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Toolbar, type ToolbarAction } from "@/components/layout/Toolbar"
import { cn } from "@/lib/utils"

interface UserProfile {
  name: string
  email: string
  initials: string
  avatar?: string
}

interface UserPreferences {
  theme: 'dark' | 'light' | 'system'
  language: string
}

function ProfileContent() {
  const searchParams = useSearchParams()
  const defaultTab = searchParams?.get('tab') || 'profile'

  const [activeTab, setActiveTab] = useState(defaultTab)
  const [profile, setProfile] = useState<UserProfile>({
    name: 'User Name',
    email: 'user@ravenhelm.ai',
    initials: 'UN',
  })
  const [preferences, setPreferences] = useState<UserPreferences>({
    theme: 'dark',
    language: 'en',
  })
  const [hasChanges, setHasChanges] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Load from localStorage
  useEffect(() => {
    const savedProfile = localStorage.getItem('userProfile')
    if (savedProfile) {
      try {
        setProfile(JSON.parse(savedProfile))
      } catch (e) {
        console.error('Failed to parse user profile:', e)
      }
    }

    const savedPreferences = localStorage.getItem('userPreferences')
    if (savedPreferences) {
      try {
        setPreferences(JSON.parse(savedPreferences))
      } catch (e) {
        console.error('Failed to parse user preferences:', e)
      }
    }
  }, [])

  const handleProfileChange = (field: keyof UserProfile, value: string) => {
    setProfile(prev => {
      const updated = { ...prev, [field]: value }

      // Auto-generate initials from name
      if (field === 'name') {
        const nameParts = value.trim().split(' ')
        updated.initials = nameParts
          .map(part => part[0])
          .filter(Boolean)
          .slice(0, 2)
          .join('')
          .toUpperCase() || 'U'
      }

      return updated
    })
    setHasChanges(true)
  }

  const handlePreferenceChange = (field: keyof UserPreferences, value: string) => {
    setPreferences(prev => ({ ...prev, [field]: value }))
    setHasChanges(true)
  }

  const handleAvatarUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      alert('Image size should be less than 2MB')
      return
    }

    const reader = new FileReader()
    reader.onloadend = () => {
      setProfile(prev => ({ ...prev, avatar: reader.result as string }))
      setHasChanges(true)
    }
    reader.readAsDataURL(file)
  }

  const handleRemoveAvatar = () => {
    setProfile(prev => ({ ...prev, avatar: undefined }))
    setHasChanges(true)
  }

  const handleSave = async () => {
    setIsSaving(true)

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500))

    // Save to localStorage
    localStorage.setItem('userProfile', JSON.stringify(profile))
    localStorage.setItem('userPreferences', JSON.stringify(preferences))

    setHasChanges(false)
    setIsSaving(false)

    // Show success message (you can use a toast here)
    console.log('Profile saved successfully')
  }

  const toolbarActions: ToolbarAction[] = [
    {
      icon: Save,
      label: 'Save Changes',
      onClick: handleSave,
      variant: 'default',
      disabled: !hasChanges || isSaving,
      tooltip: hasChanges ? 'Save your changes' : 'No changes to save',
    },
  ]

  return (
    <div className="flex flex-col h-full">
      <Toolbar actions={toolbarActions} />

      <div className="flex-1 overflow-auto">
        <div className="max-w-4xl mx-auto p-8">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-fg-0 mb-2">Profile Settings</h1>
            <p className="text-fg-2">
              Manage your account information and preferences
            </p>
          </div>

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="bg-bg-1">
              <TabsTrigger value="profile" className="gap-2">
                <User className="w-4 h-4" />
                Profile
              </TabsTrigger>
              <TabsTrigger value="preferences" className="gap-2">
                <Palette className="w-4 h-4" />
                Preferences
              </TabsTrigger>
            </TabsList>

            {/* Profile Tab */}
            <TabsContent value="profile" className="space-y-6">
              <Card className="p-6">
                <h2 className="text-xl font-semibold text-fg-0 mb-6">Personal Information</h2>

                {/* Avatar Upload */}
                <div className="mb-8">
                  <Label className="text-sm font-medium text-fg-1 mb-3 block">
                    Profile Picture
                  </Label>
                  <div className="flex items-center gap-6">
                    <div className="relative">
                      <Avatar className="w-24 h-24">
                        {profile.avatar && (
                          <AvatarImage src={profile.avatar} alt={profile.name} />
                        )}
                        <AvatarFallback className="bg-blue-600 text-white text-2xl font-semibold">
                          {profile.initials}
                        </AvatarFallback>
                      </Avatar>
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className={cn(
                          "absolute bottom-0 right-0 p-2 rounded-full",
                          "bg-blue-600 hover:bg-blue-700 text-white",
                          "shadow-lg transition-colors"
                        )}
                        aria-label="Upload picture"
                      >
                        <Camera className="w-4 h-4" />
                      </button>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={handleAvatarUpload}
                      />
                    </div>
                    <div className="flex flex-col gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => fileInputRef.current?.click()}
                      >
                        Upload Picture
                      </Button>
                      {profile.avatar && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleRemoveAvatar}
                          className="text-red-500 hover:text-red-600"
                        >
                          Remove Picture
                        </Button>
                      )}
                      <p className="text-xs text-fg-2 mt-1">
                        JPG, PNG or GIF. Max size 2MB.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Name */}
                <div className="mb-6">
                  <Label htmlFor="name" className="text-sm font-medium text-fg-1 mb-2 block">
                    Full Name
                  </Label>
                  <Input
                    id="name"
                    type="text"
                    value={profile.name}
                    onChange={(e) => handleProfileChange('name', e.target.value)}
                    placeholder="Enter your full name"
                    className="max-w-md"
                  />
                </div>

                {/* Email */}
                <div className="mb-6">
                  <Label htmlFor="email" className="text-sm font-medium text-fg-1 mb-2 block">
                    Email Address
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    value={profile.email}
                    onChange={(e) => handleProfileChange('email', e.target.value)}
                    placeholder="Enter your email address"
                    className="max-w-md"
                  />
                  <p className="text-xs text-fg-2 mt-1">
                    This email will be used for notifications and account recovery.
                  </p>
                </div>
              </Card>
            </TabsContent>

            {/* Preferences Tab */}
            <TabsContent value="preferences" className="space-y-6">
              <Card className="p-6">
                <h2 className="text-xl font-semibold text-fg-0 mb-6">Application Preferences</h2>

                {/* Theme Selector */}
                <div className="mb-6">
                  <Label htmlFor="theme" className="text-sm font-medium text-fg-1 mb-2 block">
                    Theme
                  </Label>
                  <Select
                    value={preferences.theme}
                    onValueChange={(value) => handlePreferenceChange('theme', value)}
                  >
                    <SelectTrigger id="theme" className="max-w-md">
                      <SelectValue placeholder="Select theme" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="dark">Dark</SelectItem>
                      <SelectItem value="light">Light</SelectItem>
                      <SelectItem value="system">System</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-fg-2 mt-1">
                    Choose your preferred color theme for the application.
                  </p>
                </div>

                {/* Language Selector */}
                <div className="mb-6">
                  <Label htmlFor="language" className="text-sm font-medium text-fg-1 mb-2 block">
                    Language
                  </Label>
                  <Select
                    value={preferences.language}
                    onValueChange={(value) => handlePreferenceChange('language', value)}
                  >
                    <SelectTrigger id="language" className="max-w-md">
                      <SelectValue placeholder="Select language" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="es">Español</SelectItem>
                      <SelectItem value="fr">Français</SelectItem>
                      <SelectItem value="de">Deutsch</SelectItem>
                      <SelectItem value="ja">日本語</SelectItem>
                      <SelectItem value="zh">中文</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-fg-2 mt-1">
                    Select your preferred language for the interface.
                  </p>
                </div>
              </Card>

              {/* Additional Preferences - Extensible Section */}
              <Card className="p-6">
                <h2 className="text-xl font-semibold text-fg-0 mb-2">Additional Settings</h2>
                <p className="text-sm text-fg-2">
                  More preferences coming soon...
                </p>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}

export default function ProfilePage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-full">
        <div className="text-fg-2">Loading...</div>
      </div>
    }>
      <ProfileContent />
    </Suspense>
  )
}
