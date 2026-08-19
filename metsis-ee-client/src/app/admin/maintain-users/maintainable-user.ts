export class MaintainableUser {

  public static createInstance(maintainableUser: MaintainableUser): MaintainableUser {
    return new MaintainableUser(maintainableUser.id, maintainableUser.name, maintainableUser.privileges);
  }

  constructor(public id: string, public name: string, public privileges: string[]) {
  }

  public hasPrivilege(privilege: string): boolean {
    return this.privileges.indexOf(privilege) != -1;
  }

  public togglePrivilege(privilege: string) {
    if (this.hasPrivilege(privilege)) {
      this.privileges.splice(this.privileges.indexOf(privilege), 1);
    } else {
      this.privileges.push(privilege);
    }
  }
}
