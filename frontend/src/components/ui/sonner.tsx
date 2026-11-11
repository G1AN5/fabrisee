import { Toaster as Sonner, type ToasterProps } from "sonner";

/** Toast messages (success after a change, plain-language errors). */
function Toaster(props: ToasterProps) {
  return (
    <Sonner
      theme="light"
      position="bottom-right"
      closeButton
      toastOptions={{
        duration: 5000,
        classNames: {
          toast:
            "!rounded-lg !border !border-border !bg-card !text-foreground !shadow-lg !font-sans",
          title: "!text-sm !font-medium",
          description: "!text-sm !text-muted-foreground",
        },
      }}
      {...props}
    />
  );
}

export { Toaster };
