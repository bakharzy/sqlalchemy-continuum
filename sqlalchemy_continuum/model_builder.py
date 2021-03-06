from copy import copy
import sqlalchemy as sa
from sqlalchemy_utils.functions import primary_keys, declarative_base
from .expression_reflector import ClassExpressionReflector
from .version import VersionClassBase


class ModelBuilder(object):
    """
    VersionedModelBuilder handles the building of History models based on
    parent table attributes and versioning configuration.
    """
    def __init__(self, versioning_manager, model):
        """
        :param versioning_manager:
            VersioningManager object
        :param model:
            SQLAlchemy declarative model object that acts as a parent for the
            built history model
        """
        self.manager = versioning_manager
        self.model = model

    def option(self, name):
        return self.manager.option(self.model, name)

    def build_parent_relationship(self):
        """
        Builds a relationship between currently built history class and
        parent class (the model whose history the currently build history
        class represents).
        """
        conditions = []
        foreign_keys = []
        for primary_key in primary_keys(self.model):
            conditions.append(
                getattr(self.model, primary_key.name)
                ==
                getattr(self.history_class, primary_key.name)
            )
            foreign_keys.append(
                getattr(self.history_class, primary_key.name)
            )

        # We need to check if versions relation was already set for parent
        # class.
        if not hasattr(self.model, 'versions'):
            self.model.versions = sa.orm.relationship(
                self.history_class,
                primaryjoin=sa.and_(*conditions),
                foreign_keys=foreign_keys,
                lazy='dynamic',
                backref=sa.orm.backref(
                    'version_parent'
                ),
                viewonly=True
            )

    def build_transaction_relationship(self, tx_log_class):
        """
        Builds a relationship between currently built history class and
        TransactionLog class.

        :param tx_log_class: TransactionLog class
        """
        # Only define transaction relation if it doesn't already exist in
        # parent class.

        backref_name = self.manager.options['relation_naming_function'](
            self.model.__name__
        )

        transaction_column = getattr(
            self.history_class,
            self.option('transaction_column_name')
        )

        if not hasattr(self.history_class, 'transaction'):
            self.history_class.transaction = sa.orm.relationship(
                tx_log_class,
                primaryjoin=tx_log_class.id == transaction_column,
                foreign_keys=[transaction_column],
                backref=self.manager.options['relation_naming_function'](
                    self.model.__name__
                )
            )
        else:
            setattr(
                tx_log_class,
                backref_name,
                sa.orm.relationship(
                    self.history_class,
                    primaryjoin=tx_log_class.id == transaction_column,
                    foreign_keys=[transaction_column]
                )
            )

    def build_changes_relationship(self, tx_changes_class):
        """
        Builds a relationship between currently built history class and
        TransactionChanges class.

        :param tx_changes_class: TransactionChanges class
        """
        transaction_column = getattr(
            self.history_class,
            self.option('transaction_column_name')
        )

        # Only define changes relation if it doesn't already exist in
        # parent class.
        if not hasattr(self.history_class, 'changes'):
            self.history_class.changes = sa.orm.relationship(
                tx_changes_class,
                primaryjoin=(
                    tx_changes_class.transaction_id == transaction_column
                ),
                foreign_keys=[tx_changes_class.transaction_id],
                backref=self.manager.options['relation_naming_function'](
                    self.model.__name__
                )
            )

    def find_closest_versioned_parent(self):
        """
        Finds the closest versioned parent for current parent model.
        """
        for class_ in self.model.__bases__:
            if class_ in self.manager.history_class_map:
                return (self.manager.history_class_map[class_], )

    def base_classes(self):
        """
        Returns all base classes for history model.
        """
        parents = (
            self.find_closest_versioned_parent()
            or self.manager.option(self.model, 'base_classes')
            or (declarative_base(self.model), )
        )
        return parents + (VersionClassBase, )

    def inheritance_args(self):
        """
        Return mapper inheritance args for currently built history model.
        """
        if self.find_closest_versioned_parent():
            reflector = ClassExpressionReflector(self.model)
            mapper = sa.inspect(self.model)
            inherit_condition = reflector(mapper.inherit_condition)

            return {
                'inherit_condition': inherit_condition
            }
        return {}

    def build_model(self, table):
        """
        Build history model class.
        """
        mapper_args = {}
        mapper_args.update(self.inheritance_args())

        return type(
            '%sHistory' % self.model.__name__,
            self.base_classes(),
            {
                '__table__': table,
                '__mapper_args__': mapper_args
            }
        )

    def __call__(self, table, tx_log_class, tx_changes_class):
        """
        Build history model and relationships to parent model, transaction
        log model and transaction changes model.
        """
        # versioned attributes need to be copied for each child class,
        # otherwise each child class would share the same __versioned__
        # option dict
        self.model.__versioned__ = copy(self.model.__versioned__)
        self.model.__versioned__['transaction_log'] = tx_log_class
        self.model.__versioned__['transaction_changes'] = tx_changes_class
        self.model.__versioned__['manager'] = self.manager
        self.history_class = self.build_model(table)
        self.build_parent_relationship()
        self.build_transaction_relationship(tx_log_class)
        self.build_changes_relationship(tx_changes_class)
        self.model.__versioned__['class'] = self.history_class
        self.history_class.__parent_class__ = self.model
        self.history_class.__versioning_manager__ = self.manager
        self.manager.history_class_map[self.model] = self.history_class
