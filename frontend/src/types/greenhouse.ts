export interface Greenhouse {
  id: number;
  name: string | null;
}

export interface GreenhouseUser {
  id: number;
  email: string;
  name: string | null;
  is_admin: boolean;
  is_active: boolean;
  linked_at: string;
}
