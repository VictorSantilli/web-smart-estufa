/**
 * O access token fica apenas em memória (nunca em localStorage/sessionStorage), o que
 * reduz o impacto de XSS. Ao recarregar a página, a sessão é recuperada pelo cookie
 * HttpOnly de refresh, que o JavaScript não consegue ler.
 */
let accessToken: string | null = null;

export const tokenStore = {
  get: () => accessToken,
  set: (token: string | null) => {
    accessToken = token;
  },
};
