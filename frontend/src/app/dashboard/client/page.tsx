'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getMyProfile, updateMyProfile } from '@/lib/api';
import { User } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';

export default function ClientDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editForm, setEditForm] = useState({
    name: '',
    phone_number: '',
  });

  useEffect(() => {
    const loadUserData = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const userData = localStorage.getItem('user');

        if (!token || !userData) {
          router.push('/auth/login');
          return;
        }

        const parsedUser = JSON.parse(userData);
        if (parsedUser.role !== 'CLIENT') {
          router.push('/dashboard/admin');
          return;
        }

        // Obtener datos actualizados del perfil
        const profile = await getMyProfile(token);
        setUser(profile);
        setEditForm({
          name: profile.name,
          phone_number: profile.phone_number,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error al cargar datos');
      } finally {
        setLoading(false);
      }
    };

    loadUserData();
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    document.cookie = 'access_token=; path=/; max-age=0';
    document.cookie = 'user=; path=/; max-age=0';
    router.push('/auth/login');
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      await updateMyProfile(token, editForm);
      
      // Actualizar datos locales
      const updatedProfile = await getMyProfile(token);
      setUser(updatedProfile);
      
      alert('Perfil actualizado exitosamente');
      setShowEditDialog(false);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al actualizar perfil');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="text-3xl">Dashboard de Cliente</CardTitle>
                <CardDescription className="mt-2">
                  Bienvenido, {user?.name || user?.email}
                </CardDescription>
              </div>
              <div className="flex gap-2 items-center">
                <Badge variant="secondary" className="bg-blue-100 text-blue-700">
                  CLIENT
                </Badge>
                <Button variant="outline" onClick={handleLogout}>
                  Cerrar Sesión
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        )}

        {/* Perfil del Usuario */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>Mi Perfil</CardTitle>
                <CardDescription>Información de tu cuenta</CardDescription>
              </div>
              <Button onClick={() => setShowEditDialog(true)}>
                Editar Perfil
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-gray-600">Nombre Completo</Label>
                <p className="text-lg font-semibold">{user?.name}</p>
              </div>
              <div className="space-y-2">
                <Label className="text-gray-600">Teléfono</Label>
                <p className="text-lg font-semibold">{user?.phone_number}</p>
              </div>
              <div className="space-y-2">
                <Label className="text-gray-600">Email</Label>
                <p className="text-lg font-semibold">{user?.email}</p>
              </div>
              <div className="space-y-2">
                <Label className="text-gray-600">Rol</Label>
                <p className="text-lg font-semibold">{user?.role}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
              <div className="p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-gray-600">Autenticación 2FA</p>
                <p className="text-xl font-bold text-green-600 mt-1">
                  {user?.totp_verified ? '✓ Habilitada' : '✗ Deshabilitada'}
                </p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <p className="text-sm text-gray-600">Fecha de Registro</p>
                <p className="text-sm font-bold text-purple-600 mt-1">
                  {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Información de Seguridad */}
        <Card>
          <CardHeader>
            <CardTitle>Seguridad de tu Cuenta</CardTitle>
            <CardDescription>
              Tu cuenta está protegida con las siguientes medidas de seguridad
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <h3 className="font-semibold text-blue-900 mb-2">Características de Seguridad:</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-blue-800">
                <li>Autenticación de dos factores obligatoria</li>
                <li>Tokens de sesión seguros</li>
                <li>Encriptación de extremo a extremo</li>
                <li>Protección contra ataques de fuerza bruta</li>
                <li>Bloqueo temporal tras intentos fallidos</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Dialog para Editar Perfil */}
      {showEditDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Editar Perfil</CardTitle>
              <CardDescription>
                Actualiza tu información personal
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleUpdateProfile} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-name">Nombre Completo</Label>
                  <Input
                    id="edit-name"
                    value={editForm.name}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit-phone">Teléfono</Label>
                  <Input
                    id="edit-phone"
                    value={editForm.phone_number}
                    onChange={(e) => setEditForm({ ...editForm, phone_number: e.target.value })}
                    required
                  />
                </div>
                <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
                  <p className="text-xs text-gray-600">
                    <strong>Nota:</strong> El email y la contraseña no se pueden modificar desde aquí por razones de seguridad.
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button type="submit" className="flex-1">
                    Actualizar
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowEditDialog(false)}
                    className="flex-1"
                  >
                    Cancelar
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
