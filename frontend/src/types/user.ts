export interface GreenhouseRef {
  id: number;
  name: string | null;
}

export interface User {
  id: number;
  email: string;
  name: string | null;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
  greenhouses: GreenhouseRef[];
}

export interface UserCreateInput {
  email: string;
  name: string;
  password: string;
  is_admin: boolean;
  greenhouse_ids: number[];
}

export interface UserUpdateInput {
  email?: string;
  name?: string;
  password?: string;
  is_admin?: boolean;
}
