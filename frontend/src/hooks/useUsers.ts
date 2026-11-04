import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createUser,
  listUsers,
  setUserActive,
  setUserGreenhouses,
  updateUser,
  type UserListParams,
} from '@/services/userService';
import type { UserCreateInput, UserUpdateInput } from '@/types/user';

export function useUsers(params: UserListParams) {
  return useQuery({
    queryKey: ['users', params],
    queryFn: () => listUsers(params),
    placeholderData: keepPreviousData,
  });
}

function useInvalidateUsers() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ['users'] });
    queryClient.invalidateQueries({ queryKey: ['greenhouses'] });
  };
}

export function useCreateUser() {
  const invalidate = useInvalidateUsers();
  return useMutation({ mutationFn: (input: UserCreateInput) => createUser(input), onSuccess: invalidate });
}

export function useSaveUser() {
  const invalidate = useInvalidateUsers();
  return useMutation({
    mutationFn: async ({ id, input, greenhouseIds }: { id: number; input: UserUpdateInput; greenhouseIds: number[] }) => {
      await updateUser(id, input);
      return setUserGreenhouses(id, greenhouseIds);
    },
    onSuccess: invalidate,
  });
}

export function useToggleUserActive() {
  const invalidate = useInvalidateUsers();
  return useMutation({
    mutationFn: ({ id, active }: { id: number; active: boolean }) => setUserActive(id, active),
    onSuccess: invalidate,
  });
}
