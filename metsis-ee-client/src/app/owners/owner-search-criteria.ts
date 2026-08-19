export class OwnerSearchCriteria {
  constructor(public id: string, public name: string, public phone: string, public email: string, public cadastreNo) {
  }

  hasOnlyId() {
    return this.id && (!this.name && !this.phone && !this.email && !this.cadastreNo);
  }
}
