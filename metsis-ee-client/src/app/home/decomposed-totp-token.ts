export class DecomposedTotpToken {

  constructor(public userId: string, public name: string, public totpSecret: string, public token: string) {
  }

  isTotpRegistration(): boolean {
    return this.totpSecret != null;
  }
}
