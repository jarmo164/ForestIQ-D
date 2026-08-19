import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CadastreEvalutationComponent } from './cadastre-evalutation.component';

describe('CadastreEvalutationComponent', () => {
  let component: CadastreEvalutationComponent;
  let fixture: ComponentFixture<CadastreEvalutationComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CadastreEvalutationComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CadastreEvalutationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
