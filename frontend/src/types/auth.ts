export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
}

export interface CurrentUser {
  id: number;
  email: string;
  name: string | null;
  is_admin: boolean;
}
