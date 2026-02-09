"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getAllUsers, deleteUser, updateUser, register } from "@/lib/api";
import { User } from "@/lib/types";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

export default function AdminDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showRegisterDialog, setShowRegisterDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  // Estados para el formulario de registro
  const [registerForm, setRegisterForm] = useState({
    email: "",
    password: "",
    name: "",
    phone_number: "",
  });

  // Estados para el formulario de edición
  const [editForm, setEditForm] = useState({
    name: "",
    phone_number: "",
  });

  useEffect(() => {
    const loadData = async () => {
      try {
        const token = localStorage.getItem("access_token");
        const userData = localStorage.getItem("user");

        if (!token || !userData) {
          router.push("/auth/login");
          return;
        }

        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);

        if (parsedUser.role !== "ADMIN") {
          router.push("/dashboard/client");
          return;
        }

        // Cargar lista de usuarios
        const usersList = await getAllUsers(token);
        setUsers(Array.isArray(usersList) ? usersList : []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error al cargar datos");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    document.cookie = "access_token=; path=/; max-age=0";
    document.cookie = "user=; path=/; max-age=0";
    router.push("/auth/login");
  };

  const handleRegisterUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await register(registerForm);
      alert("Usuario registrado exitosamente. Debe completar el setup de 2FA.");
      setShowRegisterDialog(false);
      setRegisterForm({ email: "", password: "", name: "", phone_number: "" });

      // Recargar lista de usuarios
      const token = localStorage.getItem("access_token");
      if (token) {
        const usersList = await getAllUsers(token);
        setUsers(Array.isArray(usersList) ? usersList : []);
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : "Error al registrar usuario");
    }
  };

  const handleEditUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;

    try {
      const token = localStorage.getItem("access_token");
      if (!token) return;

      await updateUser(token, selectedUser.id, editForm);
      alert("Usuario actualizado exitosamente");
      setShowEditDialog(false);
      setSelectedUser(null);

      // Recargar lista de usuarios
      const usersList = await getAllUsers(token);
      setUsers(Array.isArray(usersList) ? usersList : []);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Error al actualizar usuario");
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm("¿Estás seguro de que deseas eliminar este usuario?")) {
      return;
    }

    try {
      const token = localStorage.getItem("access_token");
      if (!token) return;

      await deleteUser(token, userId);
      alert("Usuario eliminado exitosamente");

      // Recargar lista de usuarios
      const usersList = await getAllUsers(token);
      setUsers(Array.isArray(usersList) ? usersList : []);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Error al eliminar usuario");
    }
  };

  const openEditDialog = (user: User) => {
    setSelectedUser(user);
    setEditForm({
      name: user.name,
      phone_number: user.phone_number,
    });
    setShowEditDialog(true);
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
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="text-3xl">
                  Dashboard de Administrador
                </CardTitle>
                <CardDescription className="mt-2">
                  Bienvenido, {user?.name || user?.email}
                </CardDescription>
              </div>
              <div className="flex gap-2 items-center">
                <Badge
                  variant="secondary"
                  className="bg-purple-100 text-purple-700"
                >
                  ADMIN
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

        {/* Acciones Rápidas */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => setShowRegisterDialog(true)}
          >
            <CardHeader>
              <CardTitle className="text-lg">Registrar Nuevo Usuario</CardTitle>
              <CardDescription>
                Crear una nueva cuenta de usuario en el sistema
              </CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Gestión de Usuarios</CardTitle>
              <CardDescription>
                Total de usuarios: {Array.isArray(users) ? users.length : 0}
              </CardDescription>
            </CardHeader>
          </Card>
        </div>

        {/* Lista de Usuarios */}
        <Card>
          <CardHeader>
            <CardTitle>Usuarios Registrados</CardTitle>
            <CardDescription>
              Administra todos los usuarios del sistema
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Array.isArray(users) && users.length > 0 ? (
                users.map((u) => (
                  <div
                    key={u.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-semibold">{u.name}</p>
                        <Badge
                          variant={u.role === "ADMIN" ? "default" : "secondary"}
                        >
                          {u.role}
                        </Badge>
                        <Badge variant={!u.totp_verified ? "destructive" : "secondary"}>{!u.totp_verified ? "No Verificado" : "Verificado"}</Badge>
                      </div>
                      <p className="text-sm text-gray-600">{u.email}</p>
                      <p className="text-sm text-gray-600">{u.phone_number}</p>
                      {/* <p className="text-xs text-gray-400 mt-1">
                      2FA: {u.totp_verified ? '✓ Habilitado' : '✗ Deshabilitado'}
                    </p> */}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openEditDialog(u)}
                      >
                        Editar
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDeleteUser(u.id)}
                        disabled={u.id === user?.id}
                      >
                        Eliminar
                      </Button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No hay usuarios registrados
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Dialog para Registrar Usuario */}
      {showRegisterDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Registrar Nuevo Usuario</CardTitle>
              <CardDescription>
                Complete todos los campos para crear un nuevo usuario
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleRegisterUser} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Nombre Completo</Label>
                  <Input
                    id="name"
                    value={registerForm.name}
                    onChange={(e) =>
                      setRegisterForm({ ...registerForm, name: e.target.value })
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Teléfono</Label>
                  <Input
                    id="phone"
                    value={registerForm.phone_number}
                    onChange={(e) =>
                      setRegisterForm({
                        ...registerForm,
                        phone_number: e.target.value,
                      })
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={registerForm.email}
                    onChange={(e) =>
                      setRegisterForm({
                        ...registerForm,
                        email: e.target.value,
                      })
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Contraseña</Label>
                  <Input
                    id="password"
                    type="password"
                    value={registerForm.password}
                    onChange={(e) =>
                      setRegisterForm({
                        ...registerForm,
                        password: e.target.value,
                      })
                    }
                    required
                  />
                </div>
                <div className="flex gap-2">
                  <Button type="submit" className="flex-1">
                    Registrar
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowRegisterDialog(false)}
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

      {/* Dialog para Editar Usuario */}
      {showEditDialog && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Editar Usuario</CardTitle>
              <CardDescription>
                Actualizar información de {selectedUser.email}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleEditUser} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-name">Nombre Completo</Label>
                  <Input
                    id="edit-name"
                    value={editForm.name}
                    onChange={(e) =>
                      setEditForm({ ...editForm, name: e.target.value })
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="edit-phone">Teléfono</Label>
                  <Input
                    id="edit-phone"
                    value={editForm.phone_number}
                    onChange={(e) =>
                      setEditForm({ ...editForm, phone_number: e.target.value })
                    }
                    required
                  />
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
