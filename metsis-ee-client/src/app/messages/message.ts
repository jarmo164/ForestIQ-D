export interface Message {
  id: number;
  message: string;
  createdAt: Date;
  noticedAt: Date;
  sender: string;
  recipient: string;
}
