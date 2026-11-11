import { ApiError } from "@/lib/api";

/** A plain message for any error: the message of the API, or a general one. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "Something went wrong. Please try again.";
}
