export interface CadastreNotification {
  notificationId: number,
  notificationNumber: number,
  cadastreSubPartCode: number,
  workCode: string,
  state: number,
  processCode: string,
  damageCode: string,
  area: number,
  amountToBeCut: number,
  decision: string,
  registrationDate: number,
  confirmationDate: number,
  archived: boolean,
  archiveDate: number
}
